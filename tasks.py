from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "sample_data"


@dataclass(frozen=True)
class TaskConfig:
    name: str
    csv_path: str
    difficulty: str
    max_steps: int
    expected_issue_types: List[str]
    approval_required_actions: List[str]
    approval_policy: Dict[str, str]
    description: str


TASKS: Dict[str, TaskConfig] = {
    "easy": TaskConfig(
        name="easy",
        csv_path=str(DATA_DIR / "easy.csv"),
        difficulty="easy",
        max_steps=5,
        expected_issue_types=["missing"],
        approval_required_actions=["fill_missing"],
        approval_policy={
            "Department:fill_missing": "approved"
        },
        description="Fix a single missing categorical value."
    ),
    "medium": TaskConfig(
        name="medium",
        csv_path=str(DATA_DIR / "medium.csv"),
        difficulty="medium",
        max_steps=7,
        expected_issue_types=["missing", "duplicates", "inconsistent"],
        approval_required_actions=["fill_missing"],
        approval_policy={
            "Salary:fill_missing": "approved"
        },
        description="Handle missing values, duplicates, and inconsistent category casing."
    ),
    "hard": TaskConfig(
        name="hard",
        csv_path=str(DATA_DIR / "hard.csv"),
        difficulty="hard",
        max_steps=9,
        expected_issue_types=["missing", "duplicates", "inconsistent"],
        approval_required_actions=["fill_missing"],
        approval_policy={
            "Salary:fill_missing": "approved"
        },
        description="Resolve multiple issue types with correct approval usage and limited steps."
    ),
}


def get_task(task_name: str) -> TaskConfig:
    if task_name not in TASKS:
        raise ValueError(f"Unknown task: {task_name}")
    return TASKS[task_name]


def list_tasks() -> List[str]:
    return list(TASKS.keys())
