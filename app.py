"""
FastAPI application for the Spreadsheet Data Cleanup environment.

Exposes the OpenEnv-compatible HTTP endpoints:
    POST /reset   — start a new episode
    POST /step    — take an action
    GET  /state   — get current episode state
    GET  /tasks   — list available tasks
    GET  /        — health check
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, File, UploadFile, Form, WebSocket, WebSocketDisconnect
from pydantic import Field
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import httpx
import json
import asyncio

load_dotenv()  # picks up .env so OPENAI_API_KEY / API_BASE_URL are available

# ---------------------------------------------------------------------------
# Agent mode detection (read once at startup)
# ---------------------------------------------------------------------------
_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", os.getenv("HF_TOKEN", ""))
_API_BASE_URL   = os.getenv("API_BASE_URL", "")
_MODEL_NAME     = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
USE_LLM = bool(_OPENAI_API_KEY)

def _make_agent():
    """Return an LLMAgent if credentials are configured, else HeuristicAgent."""
    if USE_LLM:
        from inference import LLMAgent
        print(f"[AgentMode] LLM detected — model={_MODEL_NAME} base={_API_BASE_URL}", flush=True)
        return LLMAgent()
    from inference import HeuristicAgent
    print("[AgentMode] No LLM credentials — using HeuristicAgent", flush=True)
    return HeuristicAgent()

from env import SpreadsheetCleanupEnv
from models import (
    Action, EnvState, Observation, ResetRequest, ResetResponse, 
    StepResult, ReportResponse, SuiteSummary
)
from tasks import TASKS
import grader

# ---------------------------------------------------------------------------
# Connection Manager for WebSockets
# ---------------------------------------------------------------------------

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                continue

manager = ConnectionManager()


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Spreadsheet Data Cleanup — OpenEnv Environment",
    description=(
        "An OpenEnv environment that evaluates AI agents on their ability "
        "to clean messy spreadsheet data."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared environment instance (single-episode; stateful per server process)
env = SpreadsheetCleanupEnv()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["health"])
def health_check():
    """Health-check endpoint."""
    return {
        "status": "ok",
        "environment": "spreadsheet_cleanup_env",
        "version": "1.0.0",
    }


@app.get("/tasks", tags=["tasks"])
def list_tasks():
    """List all available tasks and their metadata."""
    return [
        {
            "task_id": t.task_id,
            "difficulty": t.difficulty,
            "description": t.description,
            "max_steps": t.max_steps,
            "expected_issues": t.expected_issue_types,
            "approval_required_for": t.approval_required_for,
        }
        for t in TASKS.values()
    ]


@app.post("/reset", response_model=ResetResponse, tags=["environment"])
async def reset(body: Optional[ResetRequest] = None):
    """Reset the environment with a given task."""
    if body is None:
        body = ResetRequest()
    try:
        obs = env.reset(body.task_id)
        # Log to console in judge format
        log_msg = f"[START] task={body.task_id} env=openenv model=FastAPI"
        print(log_msg, flush=True)
        # Broadcast via WebSocket
        await manager.broadcast(log_msg)
        
        return ResetResponse(observation=obs, done=False, info={"task_id": body.task_id})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/step", response_model=StepResult, tags=["environment"])
async def step(action: Action):
    """Take a single step in the environment."""
    result = env.step(action)
    obs = result.observation
    
    # Log to console in judge format
    done_val = str(result.done).lower()
    error_val = "null" # error details not present in StepResult info currently
    action_str = f"{action.action_type.value}"
    if action.column: action_str += f"({action.column})"
    
    log_msg = f"[STEP] step={obs.step_count} action={action_str} reward={result.reward:.2f} done={done_val} error={error_val}"
    print(log_msg, flush=True)
    # Broadcast via WebSocket
    await manager.broadcast(log_msg)
    
    if result.done:
        state_dict = env.state().dict()
        score = grader.grade_from_dict(state_dict)
        end_log = f"[END] success={str(score >= 0.5).lower()} steps={obs.step_count} score={score:.2f}"
        print(end_log, flush=True)
        await manager.broadcast(end_log)

    return result


@app.post("/quick_fix", response_model=List[StepResult], tags=["environment"])
async def quick_fix():
    """Run the best available agent (LLM if configured, else Heuristic) on the current episode."""
    if env._df is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call reset() first.")

    from utils import count_total_issues
    from models import Action

    agent_type = "LLM" if USE_LLM else "Heuristic"
    agent_label = f"LLM ({_MODEL_NAME})" if USE_LLM else "HeuristicAgent"

    # Broadcast which agent is about to run so the frontend / WS log shows it
    agent_msg = f"[AGENT] mode={agent_type} model={_MODEL_NAME if USE_LLM else 'rule-based'}"
    print(agent_msg, flush=True)
    await manager.broadcast(agent_msg)

    try:
        agent = _make_agent()
    except Exception as exc:
        err = f"[AGENT] Failed to initialise {agent_label}: {exc} — falling back to HeuristicAgent"
        print(err, flush=True)
        await manager.broadcast(err)
        from inference import HeuristicAgent
        agent = HeuristicAgent()
        agent_type = "Heuristic"

    state_dict = env.state().dict()
    task_id = state_dict.get("task_id", "custom")
    task_meta = TASKS[task_id].__dict__ if task_id in TASKS else None

    obs_dict = env._build_observation("").dict()
    agent.reset(obs_dict, task_meta)

    results = []
    MAX_STEPS = 30

    while not env._done and len(results) < MAX_STEPS:
        if count_total_issues(env._df) == 0:
            break

        action_dict = agent.decide(obs_dict)
        action = Action(**action_dict)

        # Loop detection (prevent alternating inspects)
        if len(results) >= 4:
            last_4 = [r.info.get("action", {}).get("action_type") for r in results[-4:]]
            if all(a == "inspect_column" for a in last_4):
                print("Loop detected in quick_fix logic (4 consecutive inspects), terminating early.", flush=True)
                if env._task:
                    env._step_count = env._task.max_steps - 1

        result = env.step(action)
        result.info["action"] = action_dict
        result.info["agent_type"] = agent_type  # pass agent type to frontend

        results.append(result)
        obs_dict = result.observation.dict()

        action_str = f"{action.action_type.value}"
        if action.column:
            action_str += f"({action.column})"

        log_msg = f"[STEP] step={result.observation.step_count} action={action_str} reward={result.reward:.2f} done={str(result.done).lower()} error=null agent={agent_type}"
        print(log_msg, flush=True)
        await manager.broadcast(log_msg)

        if result.done:
            state_dict_final = env.state().dict()
            score = grader.grade_from_dict(state_dict_final)
            end_log = f"[END] success={str(score >= 0.5).lower()} steps={state_dict_final['step_count']} score={score:.2f}"
            print(end_log, flush=True)

            final_results = (
                f"\n--- FINAL RESULTS for '{task_id}' ({agent_label}) ---\n"
                f"  Steps used   : {state_dict_final['step_count']} / {state_dict_final['max_steps']}\n"
                f"  Issues fixed : {state_dict_final['initial_issues'] - state_dict_final['issues_remaining']} / {state_dict_final['initial_issues']}\n"
                f"  Quality score: {state_dict_final['data_quality_score']}\n"
                f"  Unapproved   : {state_dict_final['unapproved_attempts']}\n"
                f"  FINAL SCORE  : {score:.2f}\n"
            )
            print(final_results, flush=True)

            await manager.broadcast(end_log)
            await manager.broadcast(" ")
            for line in final_results.strip().split('\n'):
                await manager.broadcast(line)
            break

    return results

@app.get("/state", response_model=EnvState, tags=["environment"])
def state():
    """Return current state."""
    return env.state()

@app.post("/load_data", response_model=ResetResponse, tags=["environment"])
async def load_data(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    dataset: Optional[str] = Form(None),
    auto: bool = Form(False),
):
    df = None
    try:
        if file:
            contents = await file.read()
            if file.filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(contents))
            else:
                df = pd.read_excel(io.BytesIO(contents))
        elif url:
            async with httpx.AsyncClient() as client:
                res = await client.get(url, follow_redirects=True)
                res.raise_for_status()
                df = pd.read_excel(io.BytesIO(res.content)) if url.endswith(".xlsx") else pd.read_csv(io.BytesIO(res.content))
        elif dataset and dataset in TASKS:
            obs = env.reset(dataset)
            return ResetResponse(observation=obs, done=False, info={"task_id": dataset})
        
        if df is not None:
            dataset_name = dataset or "custom"
            obs = env.load_custom_data(df, dataset_name=dataset_name)
            return ResetResponse(observation=obs, done=False, info={"task_id": dataset_name})
        raise HTTPException(status_code=400, detail="No data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/report", response_model=ReportResponse, tags=["reporting"])
def get_report():
    """Return a detailed report of the current episode."""
    state = env.state()
    score = grader.grade_from_dict(state.dict())
    return ReportResponse(
        task_id=state.task_id,
        steps_used=state.step_count,
        max_steps=state.max_steps,
        issues_fixed=state.initial_issues - state.issues_remaining,
        initial_issues=state.initial_issues,
        quality_score=state.data_quality_score,
        unapproved_attempts=state.unapproved_attempts,
        final_score=score,
        success=score >= 0.5
    )


@app.post("/run_suite", response_model=SuiteSummary, tags=["reporting"])
async def run_suite():
    """Run the best available agent on all tasks and return a summary."""
    agent_type = "LLM" if USE_LLM else "Heuristic"
    agent_label = f"LLM ({_MODEL_NAME})" if USE_LLM else "HeuristicAgent"
    suite_msg = f"[AGENT] mode={agent_type} model={_MODEL_NAME if USE_LLM else 'rule-based'} (run_suite)"
    print(suite_msg, flush=True)
    await manager.broadcast(suite_msg)

    try:
        agent = _make_agent()
    except Exception as exc:
        err = f"[AGENT] Failed to initialise {agent_label}: {exc} — falling back to HeuristicAgent"
        print(err, flush=True)
        await manager.broadcast(err)
        from inference import HeuristicAgent
        agent = HeuristicAgent()
        agent_type = "Heuristic"
    results = {}
    
    for task_id in ["easy", "medium", "hard"]:
        obs_data = env.reset(task_id)
        # Broadcast start
        start_log = f"[START] task={task_id} env=openenv model=InternalHeuristic"
        print(start_log, flush=True)
        await manager.broadcast(start_log)
        
        agent.reset(obs_data.dict(), TASKS[task_id].__dict__)
        obs_dict = obs_data.dict()
        
        action_history = []
        while not obs_dict.get("done"):
            action_dict = agent.decide(obs_dict)
            from models import Action
            action = Action(**action_dict)
            
            if len(action_history) >= 4:
                last_4 = [a.get("action_type") for a in action_history[-4:]]
                if all(a == "inspect_column" for a in last_4):
                    print(f"Loop detected in run_suite for task {task_id}, terminating early.", flush=True)
                    if env._task:
                        env._step_count = env._task.max_steps - 1
            action_history.append(action_dict)
            
            result = env.step(action)
            obs_dict = result.observation.dict()
            
            step_log = f"[STEP] step={obs_dict.get('step_count')} action={action.action_type} reward={result.reward:.2f} done={result.done} error=null"
            print(step_log, flush=True)
            await manager.broadcast(step_log)
            
            if result.done: break
            
        state = env.state()
        score = grader.grade_from_dict(state.dict())
        end_log = f"[END] success={str(score >= 0.5).lower()} steps={state.step_count} score={score:.2f}"
        print(end_log, flush=True)
        await manager.broadcast(end_log)
        
        final_results = (
            f"--- FINAL RESULTS for '{task_id}' ---\n"
            f"  Steps used   : {state.step_count} / {state.max_steps}\n"
            f"  Issues fixed : {state.initial_issues - state.issues_remaining} / {state.initial_issues}\n"
            f"  Quality score: {state.data_quality_score}\n"
            f"  Unapproved   : {state.unapproved_attempts}\n"
            f"  FINAL SCORE  : {score:.2f}"
        )
        print(final_results, flush=True)
        await manager.broadcast(" ") # empty line
        for line in final_results.split('\n'):
            await manager.broadcast(line)
            
        results[task_id] = score
        
    avg = sum(results.values()) / len(results) if results else 0
    return SuiteSummary(scores=results, average_score=round(avg, 4))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)