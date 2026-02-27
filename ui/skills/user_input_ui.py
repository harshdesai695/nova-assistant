import os
import requests
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QFileDialog
from ui.registry import register_ui_skill

@register_ui_skill(
    title="User Input Required",
    icon="⌨️",
    description="Provide additional information",
    trigger_signal="ACTIVATE_USER_INPUT_PROTOCOL"
)
class UserInputWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Input Required")
        self.resize(500, 400)
        self.setStyleSheet("""
            QWidget { background-color: #0f111a; color: white; font-family: 'Segoe UI'; }
            QTextEdit { background-color: #161925; border: 1px solid #2a2e3f; padding: 10px; }
            QPushButton { background-color: #1f2333; border: 1px solid #00f0ff; color: #00f0ff; padding: 10px; border-radius: 5px; font-weight: bold; }
            QPushButton:hover { background-color: #00f0ff; color: black; }
        """)
        layout = QVBoxLayout(self)
        self.lbl_info = QLabel("System requires additional input:")
        layout.addWidget(self.lbl_info)
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Enter text...")
        layout.addWidget(self.text_input)
        self.file_path = None
        self.lbl_file = QLabel("No file selected")
        layout.addWidget(self.lbl_file)
        btn_layout = QHBoxLayout()
        self.btn_attach = QPushButton("Attach File")
        self.btn_attach.clicked.connect(self.attach_file)
        self.btn_submit = QPushButton("Submit")
        self.btn_submit.clicked.connect(self.submit_input)
        btn_layout.addWidget(self.btn_attach)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_submit)
        layout.addLayout(btn_layout)

    def attach_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if path:
            self.file_path = path
            self.lbl_file.setText(f"Attached: {os.path.basename(path)}")

    def submit_input(self):
        text = self.text_input.toPlainText().strip()
        payload_text = text
        if self.file_path:
            payload_text += f" [Attached File Path: {self.file_path}]"
        try:
            requests.post("http://localhost:8000/chat", json={"text": payload_text})
        except Exception:
            pass
        self.close()