from core.registry import skill
import os
import json
from typing import Optional

TASK_FILE = "tasks.json"

@skill
def manage_tasks(action: str, task: Optional[str] = None) -> str:
    """
    Manage a simple personal task list.

    Args:
        action (str): The action to perform. Options: 'add', 'list', 'remove', 'clear'.
        task (Optional[str]): The task description (required for 'add' and 'remove').

    Returns:
        str: Human-readable result of the task operation.
    """
    try:
        # Ensure task file exists
        if not os.path.exists(TASK_FILE):
            with open(TASK_FILE, 'w') as f:
                json.dump([], f)

        with open(TASK_FILE, 'r') as f:
            tasks = json.load(f)

        action = action.lower()

        if action == 'add':
            if not task:
                return "Please provide a task to add."
            tasks.append(task)
            with open(TASK_FILE, 'w') as f:
                json.dump(tasks, f, indent=2)
            return f"✅ Task added: {task}"

        elif action == 'list':
            if not tasks:
                return "📭 Your task list is empty."
            formatted = "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)])
            return f"📝 Your Tasks:\n{formatted}"

        elif action == 'remove':
            if not task:
                return "Please provide the exact task to remove."
            if task in tasks:
                tasks.remove(task)
                with open(TASK_FILE, 'w') as f:
                    json.dump(tasks, f, indent=2)
                return f"❌ Task removed: {task}"
            return "Task not found in your list."

        elif action == 'clear':
            with open(TASK_FILE, 'w') as f:
                json.dump([], f)
            return "🧹 All tasks have been cleared."

        else:
            return "Invalid action. Use: add, list, remove, or clear."

    except Exception as e:
        return f"An error occurred while managing tasks: {str(e)}"