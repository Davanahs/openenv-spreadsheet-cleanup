from tasks import TASKS

print("Available tasks in registry:", list(TASKS.keys()))

for task_id, task in TASKS.items():
    print(f"\n--- Task: {task_id} ---")
    print("Description:", task.description)
    print("Dataset Path:", task.dataset_filename)
    print("Max Steps:", task.max_steps)
    print("Expected Issues:", task.expected_issue_types)
    print("Approval Needed For:", task.approval_required_for)