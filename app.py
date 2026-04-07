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

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from pydantic import Field
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import httpx

from env import SpreadsheetCleanupEnv
from models import Action, EnvState, Observation, ResetRequest, ResetResponse, StepResult
from tasks import TASKS

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
    allow_origins=["*"],
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
def reset(body: ResetRequest):
    """Reset the environment with a given task."""
    try:
        obs = env.reset(body.task_id)
        return ResetResponse(observation=obs, done=False, info={"task_id": body.task_id})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/step", response_model=StepResult, tags=["environment"])
def step(action: Action):
    """Take a single step in the environment."""
    result = env.step(action)
    return result


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