import os
import requests
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QIcon

from ui.registry import register_ui_skill

@register_ui_skill(
    title="Weather Station",
    icon="☁️",
    description="Live atmospheric conditions",
    trigger_signal="Executing get_weather" 
)
class NovaWeatherWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("N.O.V.A Atmospheric Sensors")
        self.resize(500, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #0f111a;
                font-family: 'Segoe UI';
            }
            QLineEdit {
                padding: 12px;
                border: 2px solid #2a2e3f;
                border-radius: 8px;
                background-color: #161925;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #00f0ff;
            }
            QPushButton {
                background-color: #1f2333;
                border: 1px solid #00f0ff;
                color: #00f0ff;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #00f0ff;
                color: #000000;
            }
            QLabel { color: white; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Search Bar
        search_layout = QHBoxLayout()
        self.input_city = QLineEdit()
        self.input_city.setPlaceholderText("Enter City Name...")
        self.input_city.returnPressed.connect(self.fetch_weather)
        
        btn_search = QPushButton("Search")
        btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_search.clicked.connect(self.fetch_weather)

        search_layout.addWidget(self.input_city)
        search_layout.addWidget(btn_search)
        layout.addLayout(search_layout)

        # Weather Card
        self.card = QFrame()
        self.card.setStyleSheet("""
            QFrame {
                background-color: #161925;
                border-radius: 20px;
                border: 1px solid #2a2e3f;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(10)

        # Icon / Emoji
        self.lbl_icon = QLabel("🌤️")
        self.lbl_icon.setStyleSheet("font-size: 80px; background: transparent;")
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.lbl_icon)

        # City Name
        self.lbl_city = QLabel("--")
        self.lbl_city.setStyleSheet("font-size: 32px; font-weight: bold; color: #ffffff; background: transparent;")
        self.lbl_city.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.lbl_city)

        # Temperature
        self.lbl_temp = QLabel("--°C")
        self.lbl_temp.setStyleSheet("font-size: 64px; font-weight: bold; color: #00f0ff; background: transparent;")
        self.lbl_temp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.lbl_temp)

        # Description
        self.lbl_desc = QLabel("Waiting for data...")
        self.lbl_desc.setStyleSheet("font-size: 18px; color: #8a8d9b; background: transparent; font-style: italic;")
        self.lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.lbl_desc)

        # Details Grid
        details_widget = QWidget()
        details_widget.setStyleSheet("background: transparent;")
        details_layout = QHBoxLayout(details_widget)
        
        self.lbl_humidity = self.create_detail_label("💧 Humidity", "--%")
        self.lbl_wind = self.create_detail_label("💨 Wind", "-- m/s")
        
        details_layout.addWidget(self.lbl_humidity)
        details_layout.addWidget(self.lbl_wind)
        card_layout.addWidget(details_widget)

        layout.addWidget(self.card)
        layout.addStretch()

        # Status Bar
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setStyleSheet("color: #8a8d9b; font-size: 12px;")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_status)

        # Initial fetch if triggered by auto-launch
        QTimer.singleShot(500, self.auto_fetch_if_needed)

    def create_detail_label(self, title, value):
        lbl = QLabel(f"{title}\n{value}")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("""
            background-color: #1f2333;
            border-radius: 10px;
            padding: 10px;
            color: white;
            font-weight: bold;
        """)
        return lbl

    def auto_fetch_if_needed(self):
        # We can implement logic here if we want to parse the log for the city name
        # For now, it opens ready for input or defaults to a city
        pass

    def fetch_weather(self):
        city = self.input_city.text().strip()
        if not city:
            self.lbl_status.setText("Please enter a city name.")
            return

        self.lbl_status.setText(f"Fetching weather for {city}...")
        
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            self.lbl_status.setText("Error: API Key missing in .env")
            return

        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

        try:
            response = requests.get(url)
            data = response.json()

            if response.status_code == 200:
                self.update_ui(data)
                self.lbl_status.setText("Data updated successfully.")
            else:
                self.lbl_status.setText(f"Error: {data.get('message', 'Unknown')}")

        except Exception as e:
            self.lbl_status.setText(f"Connection Error: {e}")

    def update_ui(self, data):
        name = data["name"]
        temp = int(data["main"]["temp"])
        desc = data["weather"][0]["description"].capitalize()
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        icon_code = data["weather"][0]["icon"]

        self.lbl_city.setText(name)
        self.lbl_temp.setText(f"{temp}°C")
        self.lbl_desc.setText(desc)
        
        # Update Details (Re-creating text)
        self.lbl_humidity.setText(f"💧 Humidity\n{humidity}%")
        self.lbl_wind.setText(f"💨 Wind\n{wind} m/s")

        # Set Icon based on condition
        if "01" in icon_code: self.lbl_icon.setText("☀️")
        elif "02" in icon_code: self.lbl_icon.setText("bq")
        elif "03" in icon_code or "04" in icon_code: self.lbl_icon.setText("☁️")
        elif "09" in icon_code or "10" in icon_code: self.lbl_icon.setText("🌧️")
        elif "11" in icon_code: self.lbl_icon.setText("⛈️")
        elif "13" in icon_code: self.lbl_icon.setText("❄️")
        else: self.lbl_icon.setText("🌫️")