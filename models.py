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
    target_action: Optional[str] = None
    fill_value: Optional[Any] = None


class ResetRequest(BaseModel):
    task_id: str = "easy"


class ColumnStats(BaseModel):
    name: str
    dtype: str
    total_count: int
    non_null_count: int
    missing_count: int
    unique_count: int
    top_values: List[Any]
    sample_values: List[Any]


class Issue(BaseModel):
    column: str
    type: str
    rows: List[int]


class IssuesSummary(BaseModel):
    """Frontend-compatible issues summary with flat integer counts."""
    missing: int = 0
    duplicates: int = 0
    inconsistent: int = 0


class Observation(BaseModel):
    task_id: str = ""
    message: str
    data_sample: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    total_rows: Optional[int] = None
    total_columns: Optional[int] = None
    column_stats: Optional[ColumnStats] = None
    issues_summary: IssuesSummary = Field(default_factory=IssuesSummary)
    quality_score: float = 0.0
    issues: List[Issue] = Field(default_factory=list)
    approval_status: Optional[Dict[str, bool]] = None
    step_count: int = 0
    max_steps: int = 0
    done: bool = False


class ResetResponse(BaseModel):
    observation: Observation
    done: bool = False
    info: Dict[str, Any] = Field(default_factory=dict)


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
    message: str = ""
    available_actions: List[str] = Field(default_factory=list)
    info: Dict[str, Any] = Field(default_factory=dict)


class ReportResponse(BaseModel):
    task_id: str
    steps_used: int
    max_steps: int
    issues_fixed: int
    initial_issues: int
    quality_score: float
    unapproved_attempts: int
    final_score: float
    success: bool


class SuiteSummary(BaseModel):
    scores: Dict[str, float]
    average_score: float