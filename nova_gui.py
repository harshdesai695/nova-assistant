import sys
import threading
import logging
import time
import re
import requests
from datetime import datetime
import uvicorn
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFrame, 
                             QTextEdit, QGridLayout, QStackedWidget)
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSlot
from PyQt6.QtGui import QFont

from main import app as backend_app
from client import main_loop as start_voice_client
from ui.styles import DARK_THEME
from ui.components import QTextEditLogger, StatCard, NovaMicWidget
from ui.registry import load_ui_skills, get_all_ui_skills 
from ui.settings import SettingsPage

class BackendThread(QThread):
    def run(self):
        config = uvicorn.Config(backend_app, host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(config)
        server.run()

class ClientThread(QThread):
    def run(self):
        try:
            start_voice_client()
        except Exception as e:
            logging.error(f"Voice Client Crashed: {e}")

class WorkerThread(QThread):
    def __init__(self, target, *args):
        super().__init__()
        self.target = target
        self.args = args

    def run(self):
        self.target(*self.args)

class NovaMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("N.O.V.A Desktop Assistant")
        self.resize(1280, 850)
        self.setStyleSheet(DARK_THEME)

        self.stats = {
            "commands": 0,
            "skills": 0,
            "latency_total": 0.0,
            "latency_count": 0,
            "last_request_time": 0.0
        }
        self.start_time = datetime.now()
        self.active_windows = {} 

        self.log_handler = QTextEditLogger()
        self.log_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S'))
        
        logging.getLogger("NOVA").addHandler(self.log_handler)
        logging.getLogger("CLIENT").addHandler(self.log_handler)
        logging.getLogger("uvicorn").addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.INFO)

        load_ui_skills()

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_layout = QHBoxLayout(main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.init_sidebar()
        
        self.stack = QStackedWidget()
        self.init_home_page()
        self.init_settings_page()
        
        self.main_layout.addWidget(self.stack)
        
        self.log_handler.log_signal.connect(self.process_log)

        self.uptime_timer = QTimer()
        self.uptime_timer.timeout.connect(self.update_uptime)
        self.uptime_timer.start(1000)

        self.start_system()

    def init_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(80)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 20, 10, 20)
        
        self.btn_home = QPushButton("🏠")
        self.btn_home.setObjectName("sidebar_btn")
        self.btn_home.setCheckable(True)
        self.btn_home.setChecked(True)
        self.btn_home.clicked.connect(self.show_home)
        
        self.btn_settings = QPushButton("⚙️")
        self.btn_settings.setObjectName("sidebar_btn")
        self.btn_settings.setCheckable(True)
        self.btn_settings.clicked.connect(self.show_settings)
        
        self.btn_logs = QPushButton("📝")
        self.btn_logs.setObjectName("sidebar_btn")
        self.btn_logs.setCheckable(True)

        layout.addWidget(self.btn_home)
        layout.addWidget(self.btn_logs)
        layout.addStretch()
        layout.addWidget(self.btn_settings)
        
        self.main_layout.addWidget(sidebar)

    def init_home_page(self):
        home_widget = QWidget()
        layout = QHBoxLayout(home_widget)
        layout.setContentsMargins(0,0,0,0)
        
        center_area = QWidget()
        center_layout = QVBoxLayout(center_area)
        center_layout.setContentsMargins(40, 40, 40, 40)
        center_layout.setSpacing(20)

        header = QLabel("N.O.V.A Desktop Assistant")
        header.setObjectName("header")
        center_layout.addWidget(header)

        sub_header = QLabel("Neural Operative Virtual Assistant")
        sub_header.setObjectName("subheader")
        center_layout.addWidget(sub_header)

        mic_container = QFrame()
        mic_container.setObjectName("card")
        mic_container.setMinimumHeight(350)
        mic_layout = QVBoxLayout(mic_container)
        mic_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.mic_widget = NovaMicWidget()
        mic_layout.addWidget(self.mic_widget)

        self.status_label = QLabel("Waiting for Wake Word...")
        self.status_label.setStyleSheet("color: #8a8d9b; margin-top: 20px; font-size: 16px;")
        mic_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)

        center_layout.addWidget(mic_container)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)

        # self.add_skill_btn(grid_layout, "☁️ Check Weather", 0, 0, "check weather")
        self.add_skill_btn(grid_layout, "🧮 Open Calculator", 0, 0, "open calculator")
        self.add_skill_btn(grid_layout, "📂 List Files", 0, 1, "list files")
        self.add_skill_btn(grid_layout, "🌐 Launch Browser", 1, 0, "open google")

        row, col = 1, 1
        ui_skills = get_all_ui_skills()
        
        for name, metadata in ui_skills.items():
            btn_text = f"{metadata.icon} {metadata.title}"
            btn = QPushButton(btn_text)
            btn.setObjectName("action_btn")
            btn.clicked.connect(lambda checked, n=name: self.launch_skill_window(n))
            grid_layout.addWidget(btn, row, col)
            
            col += 1
            if col > 1:
                col = 0
                row += 1

        center_layout.addLayout(grid_layout)
        center_layout.addStretch()
        
        layout.addWidget(center_area)
        
        status_panel = self.create_status_panel()
        layout.addWidget(status_panel)
        
        self.stack.addWidget(home_widget)

    def init_settings_page(self):
        settings_widget = SettingsPage(self)
        self.stack.addWidget(settings_widget)

    def create_status_panel(self):
        panel = QFrame()
        panel.setObjectName("status_panel")
        panel.setFixedWidth(350)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 40, 20, 20)
        layout.setSpacing(20)

        status_row = QHBoxLayout()
        lbl_status = QLabel("SYSTEM STATUS")
        lbl_status.setStyleSheet("color: #8a8d9b; font-weight: bold; font-size: 12px;")
        
        self.status_badge = QLabel(" ● STARTING ")
        self.status_badge.setObjectName("status_online")
        self.status_badge.setStyleSheet("color: #ffd700; background-color: #332b00; padding: 4px 8px; border-radius: 4px;")
        
        status_row.addWidget(lbl_status)
        status_row.addStretch()
        status_row.addWidget(self.status_badge)
        layout.addLayout(status_row)

        stats_grid = QGridLayout()
        stats_grid.setSpacing(10)

        self.card_skills = StatCard("Active Skills", "0")
        self.card_commands = StatCard("Commands Today", "0")
        self.card_response = StatCard("Avg Response", "0.0s")
        self.card_uptime = StatCard("Uptime", "00:00:00")

        stats_grid.addWidget(self.card_skills, 0, 0)
        stats_grid.addWidget(self.card_commands, 0, 1)
        stats_grid.addWidget(self.card_response, 1, 0)
        stats_grid.addWidget(self.card_uptime, 1, 1)

        layout.addLayout(stats_grid)

        lbl_activity = QLabel("RECENT ACTIVITY")
        lbl_activity.setStyleSheet("color: #8a8d9b; font-weight: bold; font-size: 12px; margin-top: 10px;")
        layout.addWidget(lbl_activity)

        self.console = QTextEdit()
        self.console.setObjectName("console")
        self.console.setReadOnly(True)
        layout.addWidget(self.console)
        
        return panel

    def add_skill_btn(self, layout, text, row, col, command_text):
        btn = QPushButton(text)
        btn.setObjectName("action_btn")
        btn.clicked.connect(lambda: self.execute_quick_action(command_text))
        layout.addWidget(btn, row, col)
        return btn

    def execute_quick_action(self, text):
        self.console.append(f'<span style="color:#ffffff;">User (GUI): {text}</span>')
        worker = WorkerThread(self.send_backend_request, text)
        worker.start()
        # Keep reference to avoid GC
        self.last_worker = worker

    def send_backend_request(self, text):
        try:
            requests.post("http://localhost:8000/chat", json={"text": text})
        except Exception as e:
            logging.error(f"Failed to send GUI command: {e}")

    def show_home(self):
        self.stack.setCurrentIndex(0)
        self.btn_home.setChecked(True)
        self.btn_settings.setChecked(False)

    def show_settings(self):
        self.stack.setCurrentIndex(1)
        self.btn_settings.setChecked(True)
        self.btn_home.setChecked(False)

    def start_system(self):
        self.console.append(">>> Initializing N.O.V.A System...")
        self.backend_thread = BackendThread()
        self.backend_thread.start()
        self.client_thread = ClientThread()
        self.client_thread.start()

    def update_uptime(self):
        delta = datetime.now() - self.start_time
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.card_uptime.lbl_value.setText(f"{hours:02}:{minutes:02}:{seconds:02}")

    def launch_skill_window(self, skill_name):
        metadata = get_all_ui_skills().get(skill_name)
        if not metadata:
            return

        if skill_name in self.active_windows and self.active_windows[skill_name].isVisible():
            self.active_windows[skill_name].raise_()
            self.active_windows[skill_name].activateWindow()
        else:
            window_instance = metadata.cls()
            window_instance.show()
            if hasattr(window_instance, "start_camera"):
                window_instance.start_camera()
            self.active_windows[skill_name] = window_instance
            self.console.append(f'<span style="color:#00f0ff;">[GUI] Launched: {metadata.title}</span>')

    def process_log(self, text):
        if "NOVA" in text:
            color = "#00f0ff" 
        elif "CLIENT" in text:
            color = "#ff0055"
        elif "ERROR" in text:
            color = "#ff4444"
        else:
            color = "#8a8d9b"

        formatted_text = f'<span style="color:{color};">{text}</span>'
        self.console.append(formatted_text)
        
        for name, metadata in get_all_ui_skills().items():
            if metadata.trigger_signal and metadata.trigger_signal in text:
                 QTimer.singleShot(100, lambda n=name: self.launch_skill_window(n))

        if "Brain is active" in text or "Connected Successfully" in text:
            self.status_badge.setText(" ● ONLINE ")
            self.status_badge.setStyleSheet("color: #00ff9d; background-color: #003320; padding: 4px 8px; border-radius: 4px;")

        if "Skills Registered" in text:
            match = re.search(r"(\d+)\s+Skills", text)
            if match:
                self.stats["skills"] = int(match.group(1))
                self.card_skills.lbl_value.setText(str(self.stats["skills"]))

        if "User:" in text:
            self.stats["commands"] += 1
            self.stats["last_request_time"] = time.time()
            self.card_commands.lbl_value.setText(str(self.stats["commands"]))
            
            self.status_label.setText("Processing...")
            self.mic_widget.set_state("processing")

        if "NOVA:" in text:
            if self.stats["last_request_time"] > 0:
                latency = time.time() - self.stats["last_request_time"]
                self.stats["latency_total"] += latency
                self.stats["latency_count"] += 1
                avg = self.stats["latency_total"] / self.stats["latency_count"]
                self.card_response.lbl_value.setText(f"{avg:.2f}s")
                self.stats["last_request_time"] = 0 
            
            self.status_label.setText("Waiting for Wake Word...")
            self.mic_widget.set_state("idle")

        if "Listening..." in text:
            self.status_label.setText("Listening...")
            self.mic_widget.set_state("listening")
        
        if "Heard:" in text:
             self.status_label.setText("Analyizing Audio...")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = NovaMainWindow()
    window.show()
    
    sys.exit(app.exec())