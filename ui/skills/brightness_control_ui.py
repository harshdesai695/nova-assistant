from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider
from PyQt6.QtCore import Qt
from ui.registry import register_ui_skill
import screen_brightness_control as sbc

@register_ui_skill(
    title="Brightness Control",
    icon="💡",
    description="Adjust your screen brightness level.",
    trigger_signal="BRIGHTNESS_CONTROL_UI"
)
class BrightnessControlUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Brightness Control")
        self.resize(300, 120)

        layout = QVBoxLayout()

        self.label = QLabel("Adjust Screen Brightness")
        layout.addWidget(self.label)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        try:
            current = sbc.get_brightness(display=0)[0]
        except Exception:
            current = 50
        self.slider.setValue(current)
        self.slider.valueChanged.connect(self.change_brightness)

        layout.addWidget(self.slider)
        self.setLayout(layout)

    def change_brightness(self, value: int):
        try:
            sbc.set_brightness(value, display=0)
            self.label.setText(f"Brightness: {value}%")
        except Exception:
            self.label.setText("Error adjusting brightness")
