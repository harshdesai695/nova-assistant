import os
import pkgutil
import importlib
import logging
import traceback
import time
import uuid
import re
import inspect
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from azure.core.exceptions import HttpResponseError


import skills  
from core.registry import get_all_skills
from core.llm import initialize_brain, create_session
from core.feedback_store import FeedbackStore
from core.intent_router import LocalIntentRouter
from core.cache import ResponseCache
from core.streaming import stream_from_final_text


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NOVA")

session_store = {}
feedback_store: Optional[FeedbackStore] = None
intent_router: Optional[LocalIntentRouter] = None
response_cache: Optional[ResponseCache] = None
skills_map: Dict[str, Any] = {}
session_ttl_seconds = 600
session_cleanup_interval_seconds = 60
last_cleanup_ts = 0.0
latency_samples: list[int] = []


def _percentile(values: list[int], pct: float) -> float:
    if not values:
        return 0.0
    arr = sorted(values)
    idx = int((len(arr) - 1) * pct)
    return float(arr[idx])


def _parse_skill_args(skill_name: str, text: str) -> Optional[dict]:
    lowered = text.lower()
    if skill_name == "control_brightness":
        m = re.search(r"(\d{1,3})", lowered)
        if m:
            level = max(0, min(100, int(m.group(1))))
            return {"action": "set", "value": level}
        if "dim" in lowered:
            return {"action": "decrease", "value": 20}
        if "bright" in lowered:
            return {"action": "increase", "value": 20}
        return None
    if skill_name in {"start_countdown_timer", "countdown_timer"}:
        m = re.search(r"(\d{1,4})", lowered)
        if not m:
            return None
        value = int(m.group(1))
        seconds = value * 60 if "minute" in lowered else value
        key = "duration_seconds" if skill_name == "start_countdown_timer" else "duration"
        return {key: seconds}
    if skill_name == "get_weather":
        m = re.search(r"(?:in|for)\s+([a-zA-Z\s]+)$", text.strip())
        if not m:
            return None
        return {"city": m.group(1).strip()}
    if skill_name == "capture_screenshot":
        ts = int(time.time())
        return {"file_path": f"screenshot_{ts}.png", "add_timestamp": True}
    if skill_name in {"enable_visual_system", "get_system_info"}:
        return {}
    return None

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
    global session_ttl_seconds, session_cleanup_interval_seconds, feedback_store
    global intent_router, response_cache, skills_map
    logger.info("🚀 System Boot Sequence Initiated...")
    load_dotenv(override=True)
    session_ttl_seconds = int(os.getenv("SESSION_TTL_SECONDS", "600"))
    session_cleanup_interval_seconds = int(os.getenv("SESSION_CLEANUP_INTERVAL_SECONDS", "60"))
    feedback_store = FeedbackStore(db_path=os.getenv("NOVA_FEEDBACK_DB", "nova_feedback.db"))
    intent_router = LocalIntentRouter(threshold=float(os.getenv("NOVA_INTENT_CONFIDENCE_THRESHOLD", "0.30")))
    response_cache = ResponseCache(
        max_items=int(os.getenv("NOVA_CACHE_MAX_ITEMS", "256")),
        ttl_seconds=int(os.getenv("NOVA_CACHE_TTL_SECONDS", "180")),
    )
    
    # 1. Load Skills
    load_plugins()
    tools = get_all_skills()
    skills_map = {f.__name__: f for f in tools}
    logger.info(f"🛠️  {len(tools)} Skills Registered.")

    # 2. Initialize Brain (Azure)
    try:
        initialize_brain(tools_list=tools)
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
    session_id: Optional[str] = None
    turn_index: Optional[int] = None
    client_timestamp: Optional[float] = None


class FeedbackInput(BaseModel):
    session_id: str
    rating: int
    notes: Optional[str] = None
    interaction_id: Optional[int] = None

class AIResponse(BaseModel):
    response: str
    action_taken: bool = False
    session_id: Optional[str] = None
    interaction_id: Optional[int] = None
    route_type: Optional[str] = None
    route_confidence: float = 0.0


class StreamResponse(BaseModel):
    response: str
    chunks: list[str]
    action_taken: bool = False
    session_id: Optional[str] = None
    route_type: Optional[str] = None


def cleanup_expired_sessions(now_ts: float):
    global last_cleanup_ts
    if now_ts - last_cleanup_ts < session_cleanup_interval_seconds:
        return

    expired = []
    for sid, data in session_store.items():
        if now_ts - data["last_seen"] > session_ttl_seconds:
            expired.append(sid)

    for sid in expired:
        session_store.pop(sid, None)

    last_cleanup_ts = now_ts


@app.post("/chat", response_model=AIResponse)
async def chat_endpoint(payload: UserInput):
    if feedback_store is None:
        logger.warning("Feedback store is not initialized.")

    now_ts = time.time()
    cleanup_expired_sessions(now_ts)
    session_id = payload.session_id or str(uuid.uuid4())
    user_turn = payload.turn_index if payload.turn_index is not None else 0

    if session_id not in session_store:
        try:
            session_obj = create_session()
            restored_turn_count = 0
            if feedback_store:
                try:
                    transcript = feedback_store.get_recent_interactions(session_id=session_id, limit=16)
                    if transcript and hasattr(session_obj, "load_conversation"):
                        session_obj.load_conversation(transcript)
                        restored_turn_count = len(transcript)
                        logger.info(f"Rehydrated session {session_id} with {restored_turn_count} prior turns.")
                except Exception as hydrate_err:
                    logger.warning(f"Session rehydration failed for {session_id}: {hydrate_err}")

            session_store[session_id] = {
                "session_obj": session_obj,
                "last_seen": now_ts,
                "turn_count": restored_turn_count,
            }
        except Exception:
            raise HTTPException(status_code=503, detail="Brain not initialized.")

    session_data = session_store[session_id]
    chat_session = session_data["session_obj"]
    session_data["last_seen"] = now_ts
    # Keep backend as source of truth for turn index to avoid resets after restarts.
    user_turn = int(session_data["turn_count"])
    session_data["turn_count"] = int(user_turn) + 1

    started = time.perf_counter()
    interaction_id = None
    try:
        logger.info(f"User: {payload.text}")
        route_type = "llm"
        route_confidence = 0.0

        cache_key = None
        if os.getenv("NOVA_ENABLE_CACHE", "true").lower() == "true" and response_cache is not None:
            cache_key = response_cache.key_for(payload.text, session_id=session_id)
            cached = response_cache.get(cache_key)
            if cached is not None:
                logger.info("Cache hit for request")
                return AIResponse(
                    response=cached["response"],
                    action_taken=cached.get("action_taken", False),
                    session_id=session_id,
                    route_type="cache",
                    route_confidence=1.0,
                )

        response_wrapper = None
        if os.getenv("NOVA_ENABLE_INTENT_ROUTER", "true").lower() == "true" and intent_router is not None and skills_map:
            candidate_skill, score = intent_router.route(payload.text, available_tools=skills_map.keys())
            route_confidence = score
            if candidate_skill and candidate_skill in skills_map:
                kwargs = _parse_skill_args(candidate_skill, payload.text)
                if kwargs is not None:
                    logger.info(f"Intent router matched skill={candidate_skill} confidence={score:.2f}")
                    try:
                        result = skills_map[candidate_skill](**kwargs)
                        response_wrapper = type("R", (), {
                            "text": str(result),
                            "action_taken": True,
                            "tools_called": [candidate_skill],
                            "route_type": "router",
                            "route_confidence": score,
                        })()
                        route_type = "router"
                    except Exception as skill_err:
                        logger.warning(f"Router execution failed, falling back to LLM: {skill_err}")

        if response_wrapper is None:
            response_wrapper = chat_session.send_message(payload.text)
            route_type = getattr(response_wrapper, "route_type", "llm")
            route_confidence = getattr(response_wrapper, "route_confidence", route_confidence)

        if not response_wrapper.text:
            raise ValueError("AI returned an empty response.")
            
        logger.info(f"NOVA: {response_wrapper.text}")

        latency_ms = int((time.perf_counter() - started) * 1000)
        latency_samples.append(latency_ms)
        if len(latency_samples) > 500:
            latency_samples.pop(0)
        logger.info(
            "Latency metrics | p50=%sms p95=%sms samples=%s",
            int(_percentile(latency_samples, 0.50)),
            int(_percentile(latency_samples, 0.95)),
            len(latency_samples),
        )

        if feedback_store:
            try:
                interaction_id = feedback_store.log_interaction(
                    session_id=session_id,
                    turn_index=user_turn,
                    user_text=payload.text,
                    assistant_text=response_wrapper.text,
                    tools_called=response_wrapper.tools_called,
                    action_taken=response_wrapper.action_taken,
                    success=True,
                    error_text=None,
                    latency_ms=latency_ms,
                )
            except Exception as log_err:
                logger.warning(f"Interaction logging failed: {log_err}")

        if cache_key and response_cache is not None and route_type != "cache":
            response_cache.set(
                cache_key,
                {"response": response_wrapper.text, "action_taken": response_wrapper.action_taken},
            )
        
        return AIResponse(
            response=response_wrapper.text,
            action_taken=response_wrapper.action_taken,
            session_id=session_id,
            interaction_id=interaction_id,
            route_type=route_type,
            route_confidence=route_confidence,
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
        if feedback_store:
            try:
                feedback_store.log_interaction(
                    session_id=session_id,
                    turn_index=user_turn,
                    user_text=payload.text,
                    assistant_text=friendly_error,
                    tools_called=[],
                    action_taken=False,
                    success=False,
                    error_text=error_msg,
                    latency_ms=int((time.perf_counter() - started) * 1000),
                )
            except Exception as log_err:
                logger.warning(f"Interaction logging failed: {log_err}")
        return AIResponse(response=friendly_error, action_taken=False, session_id=session_id)

    except Exception as e:
        logger.error(f"SERVER ERROR: {str(e)}")
        traceback.print_exc() 
        if feedback_store:
            try:
                feedback_store.log_interaction(
                    session_id=session_id,
                    turn_index=user_turn,
                    user_text=payload.text,
                    assistant_text="I am encountering a technical issue.",
                    tools_called=[],
                    action_taken=False,
                    success=False,
                    error_text=str(e),
                    latency_ms=int((time.perf_counter() - started) * 1000),
                )
            except Exception as log_err:
                logger.warning(f"Interaction logging failed: {log_err}")
        return AIResponse(
            response="I am encountering a technical issue.",
            action_taken=False,
            session_id=session_id,
        )


@app.post("/chat/stream", response_model=StreamResponse)
async def chat_endpoint_stream(payload: UserInput):
    response = await chat_endpoint(payload)
    chunks = stream_from_final_text(response.response)
    return StreamResponse(
        response=response.response,
        chunks=chunks,
        action_taken=response.action_taken,
        session_id=response.session_id,
        route_type=response.route_type,
    )


@app.post("/feedback")
async def feedback_endpoint(payload: FeedbackInput):
    if feedback_store is None:
        raise HTTPException(status_code=503, detail="Feedback store not initialized.")

    if payload.rating < 1 or payload.rating > 5:
        raise HTTPException(status_code=400, detail="rating must be between 1 and 5")

    try:
        if payload.interaction_id is not None:
            feedback_id = feedback_store.mark_interaction_feedback(
                interaction_id=payload.interaction_id,
                rating=payload.rating,
                notes=payload.notes,
            )
        else:
            feedback_id = feedback_store.log_feedback(
                session_id=payload.session_id,
                rating=payload.rating,
                notes=payload.notes,
                interaction_id=None,
            )
    except Exception as e:
        logger.warning(f"Feedback logging failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to store feedback")

    return {"status": "ok", "feedback_id": feedback_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)