from tasks import get_task, list_tasks

print("Available tasks:", list_tasks())

task = get_task("easy")

print("\nTask details:")
print("Name:", task.name)
print("CSV:", task.csv_path)
print("Difficulty:", task.difficulty)
print("Max steps:", task.max_steps)
print("Expected issues:", task.expected_issue_types)
print("Approval policy:", task.approval_policy)