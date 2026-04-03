from typing import Dict


def _safe_ratio(resolved: int, total: int) -> float:
    if total <= 0:
        return 1.0
    return max(0.0, min(1.0, resolved / total))


def grade_state(final_state: Dict) -> float:
    initial_missing = int(final_state.get("initial_missing", 0))
    initial_duplicates = int(final_state.get("initial_duplicates", 0))
    initial_inconsistent = int(final_state.get("initial_inconsistent", 0))

    remaining_missing = int(final_state.get("remaining_missing", 0))
    remaining_duplicates = int(final_state.get("remaining_duplicates", 0))
    remaining_inconsistent = int(final_state.get("remaining_inconsistent", 0))

    destructive_actions = int(final_state.get("destructive_actions", 0))
    approval_violations = int(final_state.get("approval_violations", 0))

    resolved_missing = max(0, initial_missing - remaining_missing)
    resolved_duplicates = max(0, initial_duplicates - remaining_duplicates)
    resolved_inconsistent = max(0, initial_inconsistent - remaining_inconsistent)

    missing_score = _safe_ratio(resolved_missing, initial_missing)
    duplicates_score = _safe_ratio(resolved_duplicates, initial_duplicates)
    inconsistent_score = _safe_ratio(resolved_inconsistent, initial_inconsistent)

    raw_score = (
        0.4 * missing_score
        + 0.3 * duplicates_score
        + 0.3 * inconsistent_score
    )

    penalty = min(0.3, (destructive_actions * 0.1) + (approval_violations * 0.1))
    final_score = raw_score - penalty

    return max(0.0, min(1.0, final_score))