import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QCheckBox, QPushButton, QFormLayout, QFrame, QMessageBox)
from PyQt6.QtCore import Qt

class SettingsPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        header = QLabel("System Configuration")
        header.setObjectName("header")
        self.layout.addWidget(header)

        self.card = QFrame()
        self.card.setObjectName("card")
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setSpacing(20)

        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(15)

        self.chk_always_on_top = QCheckBox("Keep Window Always on Top")
        self.chk_always_on_top.toggled.connect(self.toggle_always_on_top)
        self.form_layout.addRow("Window Behavior:", self.chk_always_on_top)

        self.input_endpoint = QLineEdit()
        self.input_endpoint.setPlaceholderText("https://your-resource.openai.azure.com/")
        self.input_endpoint.setStyleSheet("padding: 8px; background-color: #0f111a; border: 1px solid #2a2e3f; color: white;")
        self.form_layout.addRow("Azure Endpoint:", self.input_endpoint)

        self.input_key = QLineEdit()
        self.input_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_key.setPlaceholderText("Azure API Key")
        self.input_key.setStyleSheet("padding: 8px; background-color: #0f111a; border: 1px solid #2a2e3f; color: white;")
        self.form_layout.addRow("Azure Credential:", self.input_key)

        self.input_model = QLineEdit()
        self.input_model.setPlaceholderText("gpt-4o")
        self.input_model.setStyleSheet("padding: 8px; background-color: #0f111a; border: 1px solid #2a2e3f; color: white;")
        self.form_layout.addRow("LLM Model Name:", self.input_model)

        self.card_layout.addLayout(self.form_layout)
        self.layout.addWidget(self.card)

        self.btn_save = QPushButton("💾 Save Configuration")
        self.btn_save.setObjectName("action_btn")
        self.btn_save.clicked.connect(self.save_settings)
        self.layout.addWidget(self.btn_save)

        self.layout.addStretch()
        self.load_current_settings()

    def toggle_always_on_top(self, checked):
        if checked:
            self.main_window.setWindowFlags(self.main_window.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.main_window.setWindowFlags(self.main_window.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        self.main_window.show()

    def load_current_settings(self):
        env_path = ".env"
        if os.path.exists(env_path):
            config = {}
            with open(env_path, "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        key, val = line.strip().split("=", 1)
                        config[key] = val
            
            self.input_endpoint.setText(config.get("AZURE_INFERENCE_ENDPOINT", ""))
            self.input_key.setText(config.get("AZURE_INFERENCE_CREDENTIAL", ""))
            self.input_model.setText(config.get("LLM_MODEL", "gpt-4o"))

    def save_settings(self):
        env_path = ".env"
        new_content = ""
        
        endpoint = self.input_endpoint.text().strip()
        key = self.input_key.text().strip()
        model = self.input_model.text().strip()

        new_content += f"AZURE_INFERENCE_ENDPOINT={endpoint}\n"
        new_content += f"AZURE_INFERENCE_CREDENTIAL={key}\n"
        new_content += f"LLM_MODEL={model}\n"

        try:
            with open(env_path, "w") as f:
                f.write(new_content)
            QMessageBox.information(self, "Success", "Configuration saved. Please restart the application for changes to apply.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")