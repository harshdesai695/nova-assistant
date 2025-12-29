import cv2
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor, QPen, QFont

from ui.registry import register_ui_skill

class CameraOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.recording = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        color_main = QColor(0, 240, 255) 
        color_alert = QColor(255, 60, 60) 
        
        pen = QPen(color_main, 3)
        painter.setPen(pen)
        
        len_leg = 40
        painter.drawLine(20, 20, 20 + len_leg, 20)
        painter.drawLine(20, 20, 20, 20 + len_leg)
        painter.drawLine(w - 20, 20, w - 20 - len_leg, 20)
        painter.drawLine(w - 20, 20, w - 20, 20 + len_leg)
        painter.drawLine(20, h - 20, 20 + len_leg, h - 20)
        painter.drawLine(20, h - 20, 20, h - 20 - len_leg)
        painter.drawLine(w - 20, h - 20, w - 20 - len_leg, h - 20)
        painter.drawLine(w - 20, h - 20, w - 20, h - 20 - len_leg)

        painter.setPen(QPen(QColor(255, 255, 255, 150), 1))
        cx, cy = w // 2, h // 2
        painter.drawLine(cx - 20, cy, cx + 20, cy)
        painter.drawLine(cx, cy - 20, cx, cy + 20)
        painter.drawEllipse(cx - 50, cy - 50, 100, 100)

        painter.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        painter.setPen(color_main)
        painter.drawText(40, h - 40, "VISUAL_SYSTEM // ONLINE")
        
        timestamp = datetime.now().strftime("%H:%M:%S:%f")[:-4]
        painter.drawText(w - 180, h - 40, f"T: {timestamp}")

        if self.recording:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color_alert)
            painter.drawEllipse(w - 50, 40, 15, 15)
            painter.setPen(color_alert)
            painter.drawText(w - 100, 52, "REC")

@register_ui_skill(
    title="Open Camera",
    icon="👁️",
    description="Access visual feeds",
    trigger_signal="ACTIVATE_VISUAL_PROTOCOL_01" 
)
class NovaCameraWindow(QWidget):
    closed_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("N.O.V.A Visual Interface")
        self.resize(1000, 700)
        self.setStyleSheet("""
            QWidget { background-color: #0a0c10; }
            QPushButton {
                background-color: #1f2333;
                border: 1px solid #00f0ff;
                color: #00f0ff;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                font-family: 'Segoe UI';
            }
            QPushButton:hover { background-color: #00f0ff; color: #000; }
            QPushButton#close_btn { border-color: #ff3c3c; color: #ff3c3c; }
            QPushButton#close_btn:hover { background-color: #ff3c3c; color: #fff; }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("border: 2px solid #1f2333; background-color: #000;")
        self.video_layout = QVBoxLayout(self.video_frame)
        self.video_layout.setContentsMargins(0, 0, 0, 0)
        
        self.display_label = QLabel()
        self.display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # CRITICAL FIX: Prevent the label from forcing the window to expand
        self.display_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.video_layout.addWidget(self.display_label)
        
        self.overlay = CameraOverlay(self.display_label)
        
        self.layout.addWidget(self.video_frame)

        controls_layout = QHBoxLayout()
        
        self.btn_capture = QPushButton("CAPTURE SNAPSHOT")
        self.btn_capture.clicked.connect(self.take_snapshot)
        
        self.btn_record = QPushButton("TOGGLE RECORDING")
        self.btn_record.clicked.connect(self.toggle_recording)
        
        self.btn_close = QPushButton("TERMINATE FEED")
        self.btn_close.setObjectName("close_btn")
        self.btn_close.clicked.connect(self.close)

        controls_layout.addWidget(self.btn_capture)
        controls_layout.addWidget(self.btn_record)
        controls_layout.addStretch()
        controls_layout.addWidget(self.btn_close)
        
        self.layout.addLayout(controls_layout)

        self.capture = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        
        # Auto-start logic handled by main gui

    def start_camera(self):
        if self.capture is None:
            self.capture = cv2.VideoCapture(0)
        self.timer.start(30)

    def stop_camera(self):
        self.timer.stop()
        if self.capture:
            self.capture.release()
            self.capture = None

    def update_frame(self):
        if not self.capture: return
        
        ret, frame = self.capture.read()
        if ret:
            frame = cv2.flip(frame, 1)
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Ensure we have a valid size before scaling to prevent errors
            target_size = self.display_label.size()
            if target_size.width() > 0 and target_size.height() > 0:
                pixmap = QPixmap.fromImage(qt_image)
                scaled_pixmap = pixmap.scaled(target_size, 
                                            Qt.AspectRatioMode.KeepAspectRatio, 
                                            Qt.TransformationMode.SmoothTransformation)
                
                self.display_label.setPixmap(scaled_pixmap)
                self.overlay.resize(target_size)
                self.overlay.update()

    def toggle_recording(self):
        self.overlay.recording = not self.overlay.recording

    def take_snapshot(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"snapshot_{timestamp}.png"
        if self.display_label.pixmap():
            self.display_label.pixmap().save(filename)

    def closeEvent(self, event):
        self.stop_camera()
        self.closed_signal.emit()
        super().closeEvent(event)