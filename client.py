import requests
import speech_recognition as sr
import pyttsx3
import logging
import time
import os
import uuid
from pathlib import Path
import queue
import threading
import re
from dotenv import load_dotenv

load_dotenv(override=True)

SERVER_URL = "http://localhost:8000/chat"
STREAM_URL = "http://localhost:8000/chat/stream"
WAKE_WORD = "nova"
SESSION_FILE = os.getenv("NOVA_SESSION_FILE", ".nova_session_id")
END_PHRASES = {
    "stop listening",
    "stop",
    "cancel",
    "done",
    "exit conversation",
    "stop speaking",
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CLIENT")

VOICE_SETTINGS = {
    "rate": int(os.getenv("TTS_RATE", 190)),
    "voice_index": int(os.getenv("TTS_VOICE_INDEX", 0)),
    "energy_threshold": int(os.getenv("MIC_ENERGY_THRESHOLD", 800))
}

try:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
except Exception as e:
    logger.error(f"Failed to initialize TTS engine: {e}")


def _trim_for_voice(text: str) -> str:
    """Keep spoken responses short so the user can quickly continue talking."""
    if not text:
        return text
    max_chars = int(os.getenv("NOVA_TTS_MAX_CHARS", "220"))
    max_sentences = int(os.getenv("NOVA_TTS_MAX_SENTENCES", "2"))

    # Split into simple sentence chunks; preserve short concise responses unchanged.
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    if len(sentences) > max_sentences:
        text = " ".join(sentences[:max_sentences])

    if len(text) > max_chars:
        text = text[: max_chars - 1].rstrip() + "…"
    return text


class SpeechController:
    def __init__(self):
        self.q: "queue.Queue[str | None]" = queue.Queue()
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def _apply_voice_settings(self):
        load_dotenv(override=True)
        rate = int(os.getenv("TTS_RATE", 190))
        v_idx = int(os.getenv("TTS_VOICE_INDEX", 0))
        engine.setProperty('rate', rate)
        voices = engine.getProperty('voices')
        if 0 <= v_idx < len(voices):
            engine.setProperty('voice', voices[v_idx].id)

    def _run(self):
        while True:
            text = self.q.get()
            try:
                if text is None:
                    return
                if not text:
                    continue
                self._apply_voice_settings()
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                logger.error(f"TTS Error: {e}")
            finally:
                self.q.task_done()

    def speak_async(self, text: str):
        if not text:
            return
        trimmed = _trim_for_voice(text)
        self.q.put(trimmed)

    def interrupt(self):
        try:
            engine.stop()
        except Exception:
            pass
        # Drop any queued speech so user can continue immediately.
        while not self.q.empty():
            try:
                self.q.get_nowait()
                self.q.task_done()
            except Exception:
                break


speech = SpeechController()

def speak(text):
    if not text:
        return
    logger.info(f"Nova: {text}")
    speech.speak_async(text)


def speak_stream(chunks):
    if not chunks:
        return
    max_chunks = int(os.getenv("NOVA_TTS_MAX_CHUNKS", "2"))
    preview = " ".join([c for c in chunks[:max_chunks] if c]).strip()
    if preview:
        speech.speak_async(preview)

def listen_for_command():
    load_dotenv(override=True)
    threshold = int(os.getenv("MIC_ENERGY_THRESHOLD", 800))
    
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = False
    recognizer.energy_threshold = threshold
    recognizer.pause_threshold = 1.5 
    
    with sr.Microphone() as source:
        logger.info(f"Listening (Threshold: {threshold})...")
        try:
            audio = recognizer.listen(source, timeout=10.0, phrase_time_limit=15.0)
            text = recognizer.recognize_google(audio).lower()
            logger.info(f"Heard: {text}")
            return text
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None 
        except sr.RequestError as e:
            logger.error(f"Network error: {e}")
            return None


def _is_end_phrase(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in END_PHRASES


def _new_session_id() -> str:
    return str(uuid.uuid4())


def _load_or_create_persistent_session_id() -> str:
    p = Path(SESSION_FILE)
    try:
        if p.exists():
            sid = p.read_text(encoding="utf-8").strip()
            if sid:
                return sid
        sid = _new_session_id()
        p.write_text(sid, encoding="utf-8")
        return sid
    except Exception as e:
        logger.warning(f"Unable to persist session id file: {e}")
        return _new_session_id()

def main_loop():
    speak("System online. Ready.")
    conversation_timeout = int(os.getenv("CONVERSATION_TIMEOUT_SECONDS", "25"))
    followup_grace = int(os.getenv("FOLLOWUP_GRACE_SECONDS", "3"))
    persistent_session_id = _load_or_create_persistent_session_id()

    active_session = False
    session_id = persistent_session_id
    turn_index = 0
    last_activity_ts = 0.0
    
    while True:
        if active_session and (time.time() - last_activity_ts) > (conversation_timeout + followup_grace):
            logger.info("Conversation timed out. Returning to wake-word mode.")
            active_session = False
            session_id = persistent_session_id
            turn_index = 0

        command = listen_for_command()
        
        if not command:
            continue

        command = command.strip().lower()
        if not command:
            continue

        if active_session and _is_end_phrase(command):
            speech.interrupt()
            speak("Okay, ending conversation mode.")
            active_session = False
            session_id = persistent_session_id
            turn_index = 0
            continue

        if not active_session:
            if WAKE_WORD not in command:
                continue

            active_session = True
            session_id = persistent_session_id
            turn_index = 0
            last_activity_ts = time.time()

        clean_command = command.replace(WAKE_WORD, "").strip()
        if active_session and not clean_command:
            if command == WAKE_WORD:
                speak("Yes?")
                last_activity_ts = time.time()
            if not clean_command:
                continue

        if not clean_command:
            continue

        try:
            # If user starts a new command while speech is active, interrupt current speech.
            speech.interrupt()
            turn_index += 1
            last_activity_ts = time.time()
            payload = {
                "text": clean_command,
                "session_id": session_id,
                "turn_index": turn_index,
                "client_timestamp": time.time(),
            }

            streaming_enabled = os.getenv("NOVA_ENABLE_STREAMING", "true").lower() == "true"
            target_url = STREAM_URL if streaming_enabled else SERVER_URL
            response = requests.post(target_url, json=payload)

            if response.status_code == 200:
                data = response.json()
                reply = data.get("response")
                chunks = data.get("chunks", []) if streaming_enabled else []

                if chunks:
                    speak_stream(chunks)
                    last_activity_ts = time.time()
                elif reply:
                    speak(reply)
                    last_activity_ts = time.time()
                else:
                    speak("I heard you, but I didn't have a response.")
            else:
                error_detail = response.json().get("detail", "Unknown error")
                logger.error(f"Server Error: {error_detail}")
                speak(f"My brain is offline. {error_detail}")

        except requests.exceptions.ConnectionError:
            speak("I cannot connect to the server. Is it running?")
        except Exception as e:
            logger.error(f"General Error: {e}")
            speak("Something went wrong.")

if __name__ == "__main__":
    print("------------------------------------------------")
    print("   N.V.O.A VOICE CLIENT (Advanced Mode)      ")
    print("------------------------------------------------")
    main_loop()