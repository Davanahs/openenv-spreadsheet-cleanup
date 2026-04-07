from grader import grade_from_dict

# Fake final state (simulate a good but not perfect cleaning run)
state = {
    "task_id": "medium",
    "step_count": 15,
    "max_steps": 25,
    "data_quality_score": 0.85,
    "initial_issues": 10,
    "issues_remaining": 2,
    "actions_taken": [],
    "approved_action_types": [],
    "unapproved_attempts": 0,
    "done": True
}

score = grade_from_dict(state)

print(f"Final Score calculated by Grader: {score}")