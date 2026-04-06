from typing import List, Optional, Dict
from pydantic import BaseModel
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ActionType(str, Enum):
    fill_missing = "fill_missing"
    normalize_values = "normalize_values"
    remove_duplicates = "remove_duplicates"


class Action(BaseModel):
    action_type: ActionType = Field(
        ...,
        description="Select action to perform"
    )
    column: Optional[str] = Field(
        None,
        description="Column name (check /state -> available_actions)"
    )

class Observation(BaseModel):
    columns: List[str]
    issues: Dict
    step_count: int



class StepResult(BaseModel):
    observation: Observation
    reward: float
    done: bool
    available_actions: List[Dict] = []