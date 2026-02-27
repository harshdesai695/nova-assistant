from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QLineEdit, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
from ui.registry import register_ui_skill
import json
import os

TASK_FILE = "tasks.json"

@register_ui_skill(
    title="Task Manager",
    icon="📝",
    description="Manage your personal task list.",
    trigger_signal="📝 Your Tasks:"
)
class TaskManagerUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Task Manager")
        self.resize(400, 500)

        self.layout = QVBoxLayout()
        self.layout.setSpacing(10)

        self.label = QLabel("📝 Your Tasks")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.layout.addWidget(self.label)

        self.task_list = QListWidget()
        self.layout.addWidget(self.task_list)

        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Enter new task...")
        self.layout.addWidget(self.task_input)

        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_task)
        button_layout.addWidget(self.add_button)

        self.complete_button = QPushButton("Mark Done")
        self.complete_button.clicked.connect(self.mark_completed)
        button_layout.addWidget(self.complete_button)

        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_task)
        button_layout.addWidget(self.remove_button)

        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self.clear_tasks)
        button_layout.addWidget(self.clear_button)

        self.layout.addLayout(button_layout)

        self.setLayout(self.layout)
        self.refresh_tasks()

    def load_tasks(self):
        if not os.path.exists(TASK_FILE):
            return []
        with open(TASK_FILE, 'r') as f:
            return json.load(f)

    def save_tasks(self, tasks):
        with open(TASK_FILE, 'w') as f:
            json.dump(tasks, f, indent=2)

    def refresh_tasks(self):
        self.task_list.clear()
        tasks = self.load_tasks()
        for task in tasks:
            self.task_list.addItem(task)

    def add_task(self):
        task = self.task_input.text().strip()
        if not task:
            return
        tasks = self.load_tasks()
        tasks.append(task)
        self.save_tasks(tasks)
        self.task_input.clear()
        self.refresh_tasks()

    def remove_task(self):
        selected = self.task_list.currentRow()
        if selected < 0:
            return
        tasks = self.load_tasks()
        tasks.pop(selected)
        self.save_tasks(tasks)
        self.refresh_tasks()

    def clear_tasks(self):
        reply = QMessageBox.question(
            self,
            "Confirm Clear",
            "Are you sure you want to delete all tasks?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.save_tasks([])
            self.refresh_tasks()

    def mark_completed(self):
        selected = self.task_list.currentRow()
        if selected < 0:
            return
        tasks = self.load_tasks()
        tasks[selected] = f"✅ {tasks[selected]}"
        self.save_tasks(tasks)
        self.refresh_tasks()
