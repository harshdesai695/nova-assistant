import requests
import speech_recognition as sr
import pyttsx3
import logging
import time
import os
from dotenv import load_dotenv

load_dotenv(override=True)

SERVER_URL = "http://localhost:8000/chat"
WAKE_WORD = "nova"

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

def speak(text):
    if not text:
        return
    logger.info(f"Nova: {text}")
    try:
        load_dotenv(override=True)
        rate = int(os.getenv("TTS_RATE", 190))
        v_idx = int(os.getenv("TTS_VOICE_INDEX", 0))
        
        engine.setProperty('rate', rate)
        voices = engine.getProperty('voices')
        if 0 <= v_idx < len(voices):
            engine.setProperty('voice', voices[v_idx].id)
            
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        logger.error(f"TTS Error: {e}")

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

def main_loop():
    speak("System online. Ready.")
    
    while True:
        command = listen_for_command()
        
        if command:
            if WAKE_WORD not in command:
                continue
            clean_command = command.replace(WAKE_WORD, "").strip()
            if not clean_command:
                speak("Yes?") 
                continue

            try:
                response = requests.post(SERVER_URL, json={"text": clean_command})
                
                if response.status_code == 200:
                    data = response.json()
                    reply = data.get("response")
                    
                    if reply:
                        speak(reply)
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