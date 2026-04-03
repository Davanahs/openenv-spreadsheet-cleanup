from grader import grade_state

# fake final state (simulate perfect cleaning)
state = {
    "initial_missing": 2,
    "remaining_missing": 2,
    "initial_duplicates": 1,
    "remaining_duplicates": 1,
    "initial_inconsistent": 1,
    "remaining_inconsistent": 1,
    "destructive_actions": 1,
    "approval_violations": 1
}

score = grade_state(state)

print("Score:", score)