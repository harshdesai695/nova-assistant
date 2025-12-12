import requests
import speech_recognition as sr
import pyttsx3
import logging
import time

SERVER_URL = "http://localhost:8000/chat"
WAKE_WORD = "Nova"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CLIENT")

try:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('rate', 190) 
except Exception as e:
    logger.error(f"Failed to initialize TTS engine: {e}")

def speak(text):
    if not text:
        return
    logger.info(f"Nova: {text}")
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        logger.error(f"TTS Error: {e}")

def listen_for_command():
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8 # Wait a bit longer before cutting off
    
    with sr.Microphone() as source:
        logger.info("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5.0, phrase_time_limit=10.0)
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
                speak("Yes?") # User just said "Nova"
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
    print("   J.A.R.V.I.S VOICE CLIENT (Windows Mode)      ")
    print("------------------------------------------------")
    main_loop()