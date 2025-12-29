# ui/styles.py

DARK_THEME = """
QMainWindow {
    background-color: #0f111a; 
}

QWidget {
    font-family: 'Segoe UI', 'Roboto', sans-serif;
    color: #ffffff;
}

/* Sidebar */
QFrame#sidebar {
    background-color: #161925;
    border-right: 1px solid #2a2e3f;
}

QPushButton#sidebar_btn {
    background-color: transparent;
    border: none;
    border-left: 3px solid transparent;
    text-align: left;
    padding: 15px;
    font-size: 16px;
    color: #8a8d9b;
}

QPushButton#sidebar_btn:hover {
    background-color: #1f2333;
    color: #ffffff;
}

QPushButton#sidebar_btn:checked {
    border-left: 3px solid #00f0ff;
    background-color: #1f2333;
    color: #00f0ff;
}

/* Cards & Panels */
QFrame#card {
    background-color: #1a1d2b;
    border-radius: 12px;
    border: 1px solid #2a2e3f;
}

QFrame#status_panel {
    background-color: #161925;
    border-left: 1px solid #2a2e3f;
}

/* Console/Logs */
QTextEdit#console {
    background-color: #0a0c10;
    border: 1px solid #2a2e3f;
    border-radius: 8px;
    color: #00ff9d;
    font-family: 'Consolas', 'Courier New', monospace;
    padding: 10px;
}

/* Action Buttons */
QPushButton#action_btn {
    background-color: #2d3245;
    border: 1px solid #3d445e;
    border-radius: 8px;
    padding: 12px;
    font-size: 14px;
    font-weight: bold;
}

QPushButton#action_btn:hover {
    background-color: #3d445e;
    border-color: #00f0ff;
}

QPushButton#action_btn:pressed {
    background-color: #00f0ff;
    color: #000000;
}

/* Headers */
QLabel#header {
    font-size: 24px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#subheader {
    font-size: 14px;
    color: #8a8d9b;
}

/* Status Indicators */
QLabel#status_online {
    color: #00ff9d;
    font-weight: bold;
    background-color: #003320;
    padding: 4px 8px;
    border-radius: 4px;
}
"""