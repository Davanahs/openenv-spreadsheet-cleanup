from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    INSPECT_COLUMN = "inspect_column"
    FILL_MISSING = "fill_missing"
    NORMALIZE_VALUES = "normalize_values"
    REMOVE_DUPLICATES = "remove_duplicates"
    REQUEST_APPROVAL = "request_approval"


class FillStrategy(str, Enum):
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"
    VALUE = "value"
    FORWARD_FILL = "ffill"


class Action(BaseModel):
    action_type: ActionType
    column: Optional[str] = None
    strategy: Optional[FillStrategy] = None
    mapping: Optional[Dict[str, str]] = None
    target_action: Optional[str] = None  # Changed from ActionType to str
    fill_value: Optional[Any] = None


class ResetRequest(BaseModel):
    task_id: str


class ColumnStats(BaseModel):
    name: str
    dtype: str
    total_count: int
    non_null_count: int
    missing_count: int
    unique_count: int
    top_values: List[Any]
    sample_values: List[Any]


class Observation(BaseModel):
    message: str
    data_sample: Optional[List[Dict[str, Any]]] = None
    column_names: Optional[List[str]] = None
    total_rows: Optional[int] = None
    total_columns: Optional[int] = None
    column_stats: Optional[ColumnStats] = None
    issues_summary: Optional[Dict[str, Any]] = None
    data_quality_score: Optional[float] = None
    approval_status: Optional[Dict[str, bool]] = None
    step_count: Optional[int] = None
    max_steps: Optional[int] = None
    done: bool


class EnvState(BaseModel):
    task_id: str
    step_count: int
    max_steps: int
    data_quality_score: float
    initial_issues: int
    issues_remaining: int
    actions_taken: List[Dict[str, Any]]
    approved_action_types: List[str]
    unapproved_attempts: int
    done: bool


class StepResult(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: Dict[str, Any]