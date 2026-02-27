from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from ui.registry import register_ui_skill


@register_ui_skill(
    title="Screenshot Captured",
    icon="📸",
    description="Displays confirmation when a screenshot is successfully captured.",
    trigger_signal="Screenshot captured successfully."
)
class ScreenshotCaptureUI(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        message = QLabel("✅ Screenshot has been captured and saved successfully.")
        layout.addWidget(message)
        self.setLayout(layout)
