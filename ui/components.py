import logging
import math
import random
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import pyqtSignal, QObject, QTimer, Qt, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QRadialGradient

class QTextEditLogger(logging.Handler, QObject):
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        QObject.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg)

class StatCard(QFrame):
    def __init__(self, title, value, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #1f2333;
                border-radius: 8px;
                padding: 10px;
            }
            QLabel { background: transparent; }
        """)
        layout = QVBoxLayout(self)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("color: #8a8d9b; font-size: 12px;")
        
        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: bold;")
        
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)

class Point3D:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class NovaMicWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate_frame)
        self.timer.start(16) 
        
        self.points = []
        self.num_points = 80
        self.radius = 100
        self.base_radius = 100
        
        self.angle_x = 0.0
        self.angle_y = 0.0
        self.angle_z = 0.0
        
        self.speed_x = 0.005
        self.speed_y = 0.005
        
        self.state = "idle"
        self.main_color = QColor(0, 240, 255)
        self.pulse_phase = 0.0

        self.init_sphere_points()

    def init_sphere_points(self):
        self.points.clear()
        for i in range(self.num_points):
            inc = math.pi * (3 - math.sqrt(5))
            off = 2 / self.num_points
            
            y = i * off - 1 + (off / 2)
            r = math.sqrt(1 - y * y)
            phi = i * inc
            
            x = math.cos(phi) * r
            z = math.sin(phi) * r
            
            self.points.append(Point3D(x, y, z))

    def set_state(self, new_state):
        self.state = new_state
        if new_state == "listening":
            self.main_color = QColor(0, 255, 157)
            self.speed_x = 0.02
            self.speed_y = 0.0
            self.base_radius = 110
        elif new_state == "processing":
            self.main_color = QColor(170, 0, 255) 
            self.speed_x = 0.04
            self.speed_y = 0.04
            self.base_radius = 90
        else:
            self.main_color = QColor(0, 240, 255)
            self.speed_x = 0.005
            self.speed_y = 0.005
            self.base_radius = 100
        self.update()

    def rotate_point(self, p, sin_x, cos_x, sin_y, cos_y):
        y1 = p.y * cos_x - p.z * sin_x
        z1 = p.z * cos_x + p.y * sin_x
        
        x2 = p.x * cos_y - z1 * sin_y
        z2 = z1 * cos_y + p.x * sin_y
        
        return Point3D(x2, y1, z2)

    def animate_frame(self):
        self.angle_x += self.speed_x
        self.angle_y += self.speed_y
        
        if self.state in ["listening", "processing"]:
            self.pulse_phase += 0.1
            pulse = math.sin(self.pulse_phase) * 10
            self.radius = self.base_radius + pulse
        else:
            # Gentle breathing in idle
            self.pulse_phase += 0.05
            pulse = math.sin(self.pulse_phase) * 5
            self.radius = self.base_radius + pulse
            
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2
        
        # Draw Glow Background
        gradient = QRadialGradient(center_x, center_y, self.radius * 1.5)
        glow_color = QColor(self.main_color)
        glow_color.setAlpha(40)
        gradient.setColorAt(0, glow_color)
        gradient.setColorAt(1, Qt.GlobalColor.transparent)
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, width, height)

        sin_x = math.sin(self.angle_x)
        cos_x = math.cos(self.angle_x)
        sin_y = math.sin(self.angle_y)
        cos_y = math.cos(self.angle_y)
        
        projected_points = []
        
        # 1. Project all points
        for p in self.points:
            rot_p = self.rotate_point(p, sin_x, cos_x, sin_y, cos_y)
            
            # Simple Orthographic Projection
            screen_x = center_x + rot_p.x * self.radius
            screen_y = center_y + rot_p.y * self.radius
            
            # Store point with Z-depth for sorting/opacity
            projected_points.append((screen_x, screen_y, rot_p.z))

        # 2. Draw Connections (The "Neural" Look)
        painter.setPen(QPen(QColor(self.main_color.red(), self.main_color.green(), self.main_color.blue(), 60), 1))
        for i in range(len(projected_points)):
            x1, y1, z1 = projected_points[i]
            
            # Optimization: Only connect to nearby neighbors to reduce drawing calls
            # We only check the next few points in the list for speed
            for j in range(i + 1, min(i + 8, len(projected_points))):
                x2, y2, z2 = projected_points[j]
                
                dist_sq = (x1 - x2)**2 + (y1 - y2)**2
                if dist_sq < 1600: # Max connection distance (40 pixels)
                    painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # 3. Draw Nodes
        for px, py, pz in projected_points:
            # Depth scaling for 3D effect
            scale = 1.0 + (pz * 0.3) 
            alpha = int(150 + (pz * 100))
            alpha = max(50, min(255, alpha))
            
            node_color = QColor(self.main_color)
            node_color.setAlpha(alpha)
            painter.setBrush(QBrush(node_color))
            painter.setPen(Qt.PenStyle.NoPen)
            
            size = 3 * scale
            painter.drawEllipse(QPointF(px, py), size, size)

        # 4. Draw Center Icon
        font = QFont("Segoe UI Emoji", 24)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        
        icon = "🎤"
        if self.state == "listening": icon = "👂"
        if self.state == "processing": icon = "🧠"
        
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, icon)