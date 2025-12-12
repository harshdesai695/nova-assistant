# N.O.V.A - Neural Operative Virtual Assistant 🤖

A voice-activated AI assistant powered by Azure AI, featuring a modular plugin system for extensible skills. Think JARVIS, but for your local machine.

## 🌟 Features

- **Voice-Activated**: Wake word detection ("Nova") with hands-free interaction
- **Azure AI Powered**: Leverages Azure's advanced language models for intelligent responses
- **Plugin Architecture**: Easily extensible skill system for adding new capabilities
- **Real-Time Speech**: Speech recognition and text-to-speech for natural conversations
- **RESTful API**: FastAPI backend for scalable, async request handling

## 🏗️ Project Structure

```
nova-assistant/
│
├── main.py                 # FastAPI server & plugin loader
├── client.py              # Voice interface client
├── check_models.py        # Azure connectivity test utility
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
├── .gitignore            # Git ignore rules
│
├── core/
│   ├── llm.py            # Azure AI integration
│   └── registry.py       # Skill registration system
│
└── skills/               # Plugin directory
    ├── __init__.py
    └── [your_skill].py   # Custom skills go here
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **Azure Account** with AI Inference access
- **Microphone** for voice input
- **Speakers** for audio output

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
   ```
   
   *(See section below on how to obtain these credentials)*

### Running the Application

1. **Test your Azure connection**
   ```bash
   python check_models.py
   ```
   
   You should see:
   ```
   ✅ Credentials Found.
   🧠 Sending test message ('Hello')...
   ✅ SUCCESS! Brain is active.
   ```

2. **Start the backend server**
   ```bash
   python main.py
   ```
   
   The server will start on `http://localhost:8000`

3. **Start the voice client** (in a new terminal)
   ```bash
   # Activate venv first
   python client.py
   ```

4. **Talk to N.O.V.A!**
   - Say: **"Nova, what's the weather today?"**
   - Say: **"Nova, tell me a joke"**
   - Say: **"Nova, what can you do?"**

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

Copy the following values:

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
```

## 🛠️ Adding New Skills

Skills are plugins that extend N.O.V.A's capabilities. Here's how to create one:

### Step 1: Create a New Skill File

Create a new Python file in the `skills/` directory:

```bash
skills/my_custom_skill.py
```

### Step 2: Define Your Skill

```python
from core.registry import register_skill

@register_skill(
    name="get_current_time",
    description="Returns the current time in 12-hour format"
)
def get_current_time():
    """Get the current time."""
    from datetime import datetime
    now = datetime.now()
    return now.strftime("%I:%M %p")
```

### Step 3: Skill with Parameters

```python
from core.registry import register_skill

@register_skill(
    name="calculate_tip",
    description="Calculate tip amount for a bill",
    parameters={
        "bill_amount": {
            "type": "number",
            "description": "The total bill amount in dollars"
        },
        "tip_percentage": {
            "type": "number",
            "description": "Tip percentage (e.g., 15, 18, 20)"
        }
    }
)
def calculate_tip(bill_amount: float, tip_percentage: float):
    """Calculate the tip amount."""
    tip = (bill_amount * tip_percentage) / 100
    total = bill_amount + tip
    return f"Tip: ${tip:.2f}, Total: ${total:.2f}"
```

### Step 4: Restart the Server

The skill will be automatically loaded when you restart `main.py`:

```bash
python main.py
```

You'll see:
```
✅ Active: skills.my_custom_skill
🛠️ 3 Skills Registered.
```

### Step 5: Test Your Skill

```bash
# In the voice client
"Nova, what time is it?"
"Nova, calculate a tip for a $50 bill with 20% tip"
```

### Skill Best Practices

1. **Keep skills focused**: One skill should do one thing well
2. **Add clear descriptions**: Help the AI understand when to use your skill
3. **Handle errors gracefully**: Use try-except blocks
4. **Return strings**: Always return human-readable responses
5. **Use type hints**: Makes your code more maintainable

### Example: Weather Skill

```python
from core.registry import register_skill
import requests

@register_skill(
    name="get_weather",
    description="Get current weather for a city",
    parameters={
        "city": {
            "type": "string",
            "description": "City name (e.g., 'London', 'New York')"
        }
    }
)
def get_weather(city: str):
    """Fetch weather data for a given city."""
    try:
        # Replace with your weather API
        api_key = "your_api_key"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        
        response = requests.get(url)
        data = response.json()
        
        temp = data['main']['temp']
        description = data['weather'][0]['description']
        
        return f"The weather in {city} is {description} with a temperature of {temp}°C"
    except Exception as e:
        return f"Sorry, I couldn't fetch the weather for {city}"
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingSkill`)
3. Commit your changes (`git commit -m 'Add some AmazingSkill'`)
4. Push to the branch (`git push origin feature/AmazingSkill`)
5. Open a Pull Request

## 📚 Resources

- [Azure AI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SpeechRecognition Library](https://pypi.org/project/SpeechRecognition/)

---

**Built with ❤️ using Azure AI and Python**