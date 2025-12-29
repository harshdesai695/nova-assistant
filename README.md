# N.O.V.A - Neural Operative Virtual Assistant 🤖

A sophisticated AI assistant powered by Azure AI, featuring both a modern desktop GUI and voice-activated interface with an extensible plugin system. Think JARVIS, but for your local machine.

## 🌟 Key Features

### 🎯 Dual Interface System
- **Desktop GUI**: Modern PyQt6 interface with real-time visualization and control
- **Voice Interface**: Hands-free interaction with wake word detection ("Nova")
- **Unified Backend**: FastAPI server handles both interfaces seamlessly

### 🧠 Intelligence & Integration
- **Azure AI Powered**: Leverages Azure's advanced language models (GPT-4o)
- **Plugin Architecture**: Easily extensible skill system for adding capabilities
- **Tool Calling**: AI autonomously selects and executes the right tools
- **Real-Time Speech**: Speech recognition and text-to-speech for natural conversations

### 🎨 Advanced GUI Features
- **3D Animated Visualization**: Neural network-inspired sphere with state indicators
- **Live Statistics**: Commands, response times, uptime, and system metrics
- **Modular UI Skills**: Camera feeds, weather displays, and custom windows
- **Real-Time Console**: Live logs from backend, voice client, and AI operations
- **Settings Manager**: Configure Azure credentials and system behavior

### 🛠️ Built-in Skills
- **System Operations**: Calculator, file management, app launching
- **System Information**: CPU, memory, disk, battery, network stats
- **Weather Integration**: Live weather data with visual UI
- **Camera Access**: Computer vision capabilities with HUD overlay
- **Web Operations**: Browser automation and website launching

## 🏗️ Project Architecture

```
nova-assistant/
│
├── main.py                     # FastAPI backend server
├── nova_gui.py                 # PyQt6 desktop interface (main entry point)
├── client.py                   # Voice interface client
├── check_models.py             # Azure connectivity test utility
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (create this)
├── .gitignore                  # Git ignore rules
│
├── core/                       # Core system modules
│   ├── llm.py                  # Azure AI integration & tool calling
│   └── registry.py             # Skill registration system
│
├── skills/                     # Backend skill plugins
│   ├── __init__.py
│   ├── app_launcher.py         # Application launching
│   ├── camera_ops.py           # Camera control
│   ├── file_ops.py             # File operations
│   ├── os_ops.py               # OS-level operations
│   ├── system_info.py          # System monitoring
│   ├── weather_ops.py          # Weather API integration
│   └── web_ops.py              # Web automation
│
└── ui/                         # GUI modules
    ├── components.py           # Reusable UI components
    ├── registry.py             # UI skill registration
    ├── styles.py               # Dark theme stylesheet
    ├── settings.py             # Settings page
    └── skills/                 # UI skill windows
        ├── camera_ui.py        # Camera interface
        └── weather_ui.py       # Weather interface
```

## 🚀 Quick Start Guide

### Prerequisites

- **Python 3.8+**
- **Azure Account** with AI Inference access
- **Microphone** for voice input
- **Speakers** for audio output
- **Webcam** (optional, for camera features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/nova-assistant.git
   cd nova-assistant
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file**
   ```bash
   # Create a new file named .env in the root directory
   touch .env  # macOS/Linux
   # or manually create it on Windows
   ```

5. **Add your Azure credentials to `.env`**
   ```env
   AZURE_INFERENCE_ENDPOINT=your_endpoint_here
   AZURE_INFERENCE_CREDENTIAL=your_api_key_here
   LLM_MODEL=gpt-4o
   OPENWEATHER_API_KEY=your_weather_api_key  # Optional, for weather features
   ```

### Running the Application

#### Option 1: Unified Desktop App (Recommended)
```bash
python nova_gui.py
```

This launches the complete system:
- ✅ Modern desktop GUI with visualization
- ✅ Backend server (FastAPI)
- ✅ Voice client (automatic)
- ✅ All features in one window

**What you get:**
- Real-time activity console
- Voice interaction with visual feedback
- Quick action buttons
- System statistics dashboard
- Settings manager

#### Option 2: Traditional Separate Mode

**Terminal 1 - Backend Server:**
```bash
python main.py
```

**Terminal 2 - Voice Client:**
```bash
python client.py
```

**Using the System:**
- Say: **"Nova, what's the weather today?"**
- Say: **"Nova, tell me a joke"**
- Say: **"Nova, what can you do?"**
- Say: **"Nova, open the camera"**
- Say: **"Nova, what's my CPU usage?"**

## 🔑 Getting Azure Credentials

### Step 1: Create an Azure Account
1. Go to [Azure Portal](https://portal.azure.com)
2. Sign up for a free account (includes $200 credit for 30 days)

### Step 2: Create an Azure AI Resource

#### Option A: Azure AI Foundry (Recommended)
1. Navigate to [Azure AI Foundry](https://ai.azure.com)
2. Click **"+ New project"**
3. Fill in:
   - **Project name**: `nova-assistant`
   - **Hub**: Create new or select existing
   - **Region**: Choose closest to you
4. Click **"Create"**
5. Once created, go to **"Project Settings"** → **"Keys and Endpoints"**

#### Option B: Azure OpenAI Service
1. In Azure Portal, search for **"Azure OpenAI"**
2. Click **"+ Create"**
3. Fill in the form:
   - **Subscription**: Your subscription
   - **Resource group**: Create new or use existing
   - **Region**: Select available region
   - **Name**: `nova-openai-resource`
   - **Pricing tier**: Standard S0
4. Click **"Review + Create"** → **"Create"**
5. Wait for deployment (2-3 minutes)
6. Go to your resource → **"Keys and Endpoint"**

### Step 3: Deploy a Model
1. In your resource, go to **"Model deployments"**
2. Click **"+ Create new deployment"**
3. Select:
   - **Model**: `gpt-4o` or `gpt-4`
   - **Deployment name**: `gpt-4o-deployment`
4. Click **"Create"**

### Step 4: Get Your Credentials

**AZURE_INFERENCE_ENDPOINT:**
```
For Azure AI Foundry:
https://YOUR-PROJECT.openai.azure.com/

For Azure OpenAI:
https://YOUR-RESOURCE.openai.azure.com/openai/deployments/YOUR-DEPLOYMENT/chat/completions?api-version=2024-05-01-preview
```

**AZURE_INFERENCE_CREDENTIAL:**
```
Your API Key (32-character string)
Found under "Keys and Endpoint" → KEY 1
```

**Example `.env` file:**
```env
AZURE_INFERENCE_ENDPOINT=https://my-nova-project.openai.azure.com/
AZURE_INFERENCE_CREDENTIAL=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
LLM_MODEL=gpt-4o
OPENWEATHER_API_KEY=your_openweather_key_here
```

## 🛠️ Creating Backend Skills (Tools)

Skills extend N.O.V.A's capabilities with new actions. The AI automatically decides when to use them.

### Step 1: Create a New Skill File

Create a new Python file in the `skills/` directory:

```bash
skills/my_custom_skill.py
```

### Step 2: Simple Skill Example

```python
from core.registry import skill

@skill
def get_current_time():
    """Returns the current time in 12-hour format."""
    from datetime import datetime
    now = datetime.now()
    return now.strftime("%I:%M %p")
```

### Step 3: Skill with Parameters

```python
from core.registry import skill

@skill
def calculate_tip(bill_amount: float, tip_percentage: float):
    """
    Calculate tip amount for a bill.
    
    Args:
        bill_amount: The total bill amount in dollars
        tip_percentage: Tip percentage (e.g., 15, 18, 20)
    """
    tip = (bill_amount * tip_percentage) / 100
    total = bill_amount + tip
    return f"Tip: ${tip:.2f}, Total: ${total:.2f}"
```

### Step 4: Advanced Skill with External API

```python
from core.registry import skill
import requests

@skill
def get_stock_price(symbol: str):
    """
    Get current stock price for a given symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
    """
    try:
        # Replace with your actual API
        url = f"https://api.example.com/stock/{symbol}"
        response = requests.get(url)
        data = response.json()
        
        price = data['price']
        change = data['change']
        
        return f"{symbol} is trading at ${price}, {change}% today"
    except Exception as e:
        return f"Sorry, I couldn't fetch data for {symbol}"
```

### Skill Best Practices

1. **Use clear docstrings**: The AI reads these to understand when to use the skill
2. **Type hints**: Always provide type hints for parameters
3. **Error handling**: Use try-except blocks
4. **Return strings**: Always return human-readable text
5. **Keep focused**: One skill should do one thing well

## 🎨 Creating UI Skills (Windows)

UI Skills are custom windows that can be launched by voice or GUI button.

### Step 1: Create UI Skill File

Create a file in `ui/skills/` directory:

```bash
ui/skills/my_ui_skill.py
```

### Step 2: Basic UI Skill Template

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from ui.registry import register_ui_skill

@register_ui_skill(
    title="My Custom Tool",
    icon="🔧",
    description="Does something amazing",
    trigger_signal="ACTIVATE_MY_TOOL"  # Optional: auto-launch on this log message
)
class MyCustomWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Custom Tool")
        self.resize(600, 400)
        
        # Your UI code here
        layout = QVBoxLayout(self)
        
        label = QLabel("Hello from my custom tool!")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        btn = QPushButton("Do Something")
        btn.clicked.connect(self.do_something)
        layout.addWidget(btn)
    
    def do_something(self):
        print("Button clicked!")
```

### Step 3: UI Skill with Auto-Launch

To make the UI automatically open when a backend skill is called:

```python
# In skills/my_backend_skill.py
@skill
def activate_my_tool():
    """Activates my custom tool interface."""
    return "ACTIVATE_MY_TOOL"  # This triggers the UI to open
```

The UI will automatically open when the trigger signal appears in logs!

## 📋 Available Backend Skills

| Skill | Description | Example Usage |
|-------|-------------|---------------|
| `launch_application` | Open any installed app | "Open WhatsApp" |
| `enable_visual_system` | Activate camera | "Turn on camera" |
| `read_file` | Read file contents | "Read my notes" |
| `write_file` | Create/overwrite files | "Write a file" |
| `create_folder` | Create directories | "Make a new folder" |
| `list_files` | List directory contents | "List files in Documents" |
| `get_system_info` | Full system report | "System status" |
| `get_cpu_usage` | CPU statistics | "CPU usage" |
| `get_memory_usage` | RAM statistics | "Memory usage" |
| `get_disk_usage` | Disk statistics | "Disk space" |
| `get_battery_status` | Battery info | "Battery level" |
| `get_weather` | Weather for any city | "Weather in London" |
| `open_website` | Open URLs | "Open google.com" |

## 🎯 GUI Features Explained

### Main Dashboard
- **3D Neural Sphere**: Visual representation of AI state
  - Blue (Idle): Waiting for commands
  - Green (Listening): Recording audio
  - Purple (Processing): AI thinking
- **Statistics Cards**: Live system metrics
- **Quick Actions**: One-click commands
- **Activity Console**: Real-time logs

### Settings Page
- Configure Azure credentials without editing files
- Toggle "Always on Top" window mode
- All settings persist to `.env` file

### UI Skills System
- Camera Window: Live feed with HUD overlay
- Weather Window: Beautiful weather display
- Extensible: Add your own custom windows

## 🐛 Troubleshooting

### "Brain not initialized" error
- Check your `.env` file has correct Azure credentials
- Run `python check_models.py` to test connection
- Verify your Azure model deployment is active

### Voice recognition not working
- Ensure microphone permissions are granted
- Check microphone is set as default device
- Speak clearly after saying "Nova"
- Adjust `energy_threshold` in `client.py` if too sensitive

### Camera won't open
- Verify camera permissions
- Check another app isn't using the camera
- Try restarting the application

### GUI not starting
- Ensure PyQt6 is installed: `pip install PyQt6`
- Check for errors in console output
- Try running `python main.py` separately first

## 🔧 Advanced Configuration

### Custom Wake Word
Edit `client.py`:
```python
WAKE_WORD = "NOVA"  # Change to your preference
```

### TTS Voice & Speed
Edit `client.py`:
```python
engine.setProperty('rate', 190)  # Speed (words per minute)
engine.setProperty('voice', voices[1].id)  # Different voice
```

### Server Port
Edit `main.py`:
```python
uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
```

## 📦 Building Executable

To create a standalone `.exe` file:

```bash
pyinstaller --onefile --windowed --icon=icon.ico nova_gui.py
```

The executable will be in the `dist/` folder.

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Contribution Ideas
- New skills (Spotify control, email, calendar)
- UI improvements
- Additional language support
- Mobile companion app
- Multi-language speech recognition

## 📚 Resources & Documentation

- [Azure AI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [SpeechRecognition Library](https://pypi.org/project/SpeechRecognition/)
- [OpenCV Documentation](https://docs.opencv.org/)

## 📄 License

This project is open source and available under the MIT License.


---

<div align="center">
  Made with ❤️ by Harsh Desai
  <br/>
  <br/>
  If you found this project helpful, please consider giving it a ⭐️
</div>