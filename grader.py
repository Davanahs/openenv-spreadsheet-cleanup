"""
Grader for the Spreadsheet Data Cleanup environment.

Takes the final EnvState + environment reference and produces a
deterministic score between 0.0 and 1.0.
"""

from __future__ import annotations

from typing import Dict

from env import SpreadsheetCleanupEnv
from models import EnvState


def grade(env_state: EnvState, env: SpreadsheetCleanupEnv) -> float:
    """
    Compute a final score for a completed (or timed-out) episode.

    Score formula (weighted):
        - Issues fixed   (50 %): proportion of initial issues resolved
        - Data quality   (30 %): final data_quality_score
        - Efficiency     (10 %): (1 - steps_used / max_steps)
        - Compliance     (10 %): penalty for unapproved action attempts

    Returns a float in [0.0, 1.0].
    """
    # --- Issues fixed (50 %) ---
    if env_state.initial_issues > 0:
        issues_fixed_ratio = (
            (env_state.initial_issues - env_state.issues_remaining)
            / env_state.initial_issues
        )
    else:
        issues_fixed_ratio = 1.0
    issues_fixed_score = max(0.0, min(1.0, issues_fixed_ratio))

    # --- Data quality (30 %) ---
    quality_score = max(0.0, min(1.0, env_state.data_quality_score))

    # --- Efficiency (10 %) ---
    if env_state.max_steps > 0:
        efficiency_score = 1.0 - (env_state.step_count / env_state.max_steps)
    else:
        efficiency_score = 1.0
    efficiency_score = max(0.0, min(1.0, efficiency_score))

    # --- Compliance (10 %) ---
    if env_state.unapproved_attempts == 0:
        compliance_score = 1.0
    else:
        # Each unapproved attempt reduces compliance by 0.25 (capped at 0)
        compliance_score = max(0.0, 1.0 - 0.25 * env_state.unapproved_attempts)

    # --- Repeated Useless Actions Penalty ---
    # We consider an action useless if it yields a reward of <= 0.0
    useless_steps = sum(1 for action in env_state.actions_taken if action.get("reward", 0.0) <= 0.0)
    over_action_penalty = 0.1 if useless_steps > 3 else 0.0

    # --- Precision Bonus ---
    minimal_steps_threshold = max(3, int(env_state.max_steps * 0.5))
    precision_bonus = 0.0
    if env_state.issues_remaining == 0 and env_state.step_count <= minimal_steps_threshold:
        precision_bonus = 0.05

    # --- Weighted total ---
    final_score = (
        0.50 * issues_fixed_score
        + 0.30 * quality_score
        + 0.10 * efficiency_score
        + 0.10 * compliance_score
    )
    final_score = final_score - over_action_penalty + precision_bonus
    return float(round(max(0.0, min(1.0, float(final_score))), 4))


def grade_from_dict(state_dict: Dict) -> float:
    """Convenience: grade from a raw state dict (e.g. from the API)."""
    env_state = EnvState(**state_dict)
    # We don't need the live env object for scoring — all data is in EnvState
    return grade(env_state, env=None)  # type: ignore[arg-type]