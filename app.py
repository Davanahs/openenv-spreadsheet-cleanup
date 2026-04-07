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

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from env import SpreadsheetCleanupEnv
from models import Action, EnvState, Observation, ResetRequest, StepResult
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


@app.post("/reset", response_model=Observation, tags=["environment"])
def reset(body: ResetRequest):
    """Reset the environment with a given task."""
    try:
        obs = env.reset(body.task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return obs


@app.post("/step", response_model=StepResult, tags=["environment"])
def step(action: Action):
    """Take a single step in the environment."""
    result = env.step(action)
    return result


@app.get("/state", response_model=EnvState, tags=["environment"])
def state():
    """Return the current state of the episode."""
    return env.state()