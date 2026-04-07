"""
Task definitions for the Spreadsheet Data Cleanup environment.

Each task specifies which dataset to use, difficulty parameters,
maximum steps, and approval rules.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class TaskConfig:
    """Configuration for a single evaluation task."""

    task_id: str
    dataset_filename: str
    description: str
    max_steps: int
    approval_required_for: List[str] = field(default_factory=list)
    expected_issue_types: List[str] = field(default_factory=list)
    difficulty: str = "easy"


# Base directory where datasets live
_DATASETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets")


TASKS: Dict[str, TaskConfig] = {
    "easy": TaskConfig(
        task_id="easy",
        dataset_filename=os.path.join(_DATASETS_DIR, "easy.csv"),
        description="Simple dataset with only missing values. No approval required.",
        max_steps=20,
        approval_required_for=[],          # no approval needed
        expected_issue_types=["missing"],
        difficulty="easy",
    ),
    "medium": TaskConfig(
        task_id="medium",
        dataset_filename=os.path.join(_DATASETS_DIR, "medium.csv"),
        description=(
            "Mixed issues: missing values, duplicate rows, and inconsistent "
            "department names. No approval required."
        ),
        max_steps=25,
        approval_required_for=[],          # no approval needed
        expected_issue_types=["missing", "duplicates", "inconsistent"],
        difficulty="medium",
    ),
    "hard": TaskConfig(
        task_id="hard",
        dataset_filename=os.path.join(_DATASETS_DIR, "hard.csv"),
        description=(
            "Large dataset with all issue types plus stricter rules. "
            "Agent MUST request approval before using fill_missing or "
            "remove_duplicates."
        ),
        max_steps=30,
        approval_required_for=["fill_missing", "remove_duplicates"],
        expected_issue_types=["missing", "duplicates", "inconsistent"],
        difficulty="hard",
    ),
}


def get_task(task_id: str) -> TaskConfig:
    """Return the TaskConfig for *task_id* or raise ValueError."""
    if task_id not in TASKS:
        raise ValueError(
            f"Unknown task_id '{task_id}'. Available tasks: {list(TASKS.keys())}"
        )
    return TASKS[task_id]
