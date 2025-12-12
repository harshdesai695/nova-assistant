import os
import pkgutil
import importlib
import logging
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from azure.core.exceptions import HttpResponseError, ClientAuthenticationError


import skills  
from core.registry import get_all_skills
from core.llm import initialize_brain # Renamed from initialize_gemini


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NOVA")

chat_session = None

def load_plugins():
    logger.info("🔌 Loading Plugins...")
    package = skills
    prefix = package.__name__ + "."
    
    for _, name, _ in pkgutil.iter_modules(package.__path__, prefix):
        try:
            importlib.import_module(name)
            logger.info(f"✅ Active: {name}")
        except Exception as e:
            logger.error(f"❌ Failed to load {name}: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global chat_session
    logger.info("🚀 System Boot Sequence Initiated...")
    load_dotenv(override=True)
    
    # 1. Load Skills
    load_plugins()
    tools = get_all_skills()
    logger.info(f"🛠️  {len(tools)} Skills Registered.")

    # 2. Initialize Brain (Azure)
    try:
        chat_session = initialize_brain(tools_list=tools)
        logger.info("🧠 Azure Brain Connected Successfully.")
    except Exception as e:
        logger.critical(f"🔥 Failed to connect to Azure AI: {e}")
        traceback.print_exc()
        
    yield
    logger.info("💤 System Shutting Down...")

app = FastAPI(title="N.O.V.A Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserInput(BaseModel):
    text: str

class AIResponse(BaseModel):
    response: str
    action_taken: bool = False


@app.post("/chat", response_model=AIResponse)
async def chat_endpoint(payload: UserInput):
    global chat_session
    
    if not chat_session:
        raise HTTPException(status_code=503, detail="Brain not initialized.")

    try:
        logger.info(f"User: {payload.text}")
        response_wrapper = chat_session.send_message(payload.text)
        if not response_wrapper.text:
            raise ValueError("AI returned an empty response.")
            
        logger.info(f"NOVA: {response_wrapper.text}")
        
        return AIResponse(
            response=response_wrapper.text,
            action_taken=response_wrapper.action_taken
        )

    except HttpResponseError as e:
        error_msg = str(e)
        logger.error(f"☁️ AZURE ERROR: {error_msg}")
        
        if "429" in error_msg:
            friendly_error = "I have reached my processing limit. Please wait a moment."
        elif "401" in error_msg:
            friendly_error = "My authentication credentials seem to be invalid."
        else:
            friendly_error = "I'm having trouble connecting to the cloud."
        return AIResponse(response=friendly_error, action_taken=False)

    except Exception as e:
        logger.error(f"SERVER ERROR: {str(e)}")
        traceback.print_exc() 
        return AIResponse(
            response="I am encountering a technical issue.",
            action_taken=False
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)