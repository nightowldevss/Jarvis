import pyttsx3
import threading

VOICE_ID     = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_IT-IT_ELSA_11.0"
VOICE_RATE   = 155
VOICE_VOLUME = 1.0

_lock         = threading.Lock()
_log_callback = None

def set_log_callback(fn):
    global _log_callback
    _log_callback = fn

def speak(text):
    if not text:
        return
    if _log_callback:
        _log_callback(text, "jarvis")
    with _lock:
        for attempt in range(2):
            try:
                engine = pyttsx3.init()
                engine.setProperty("rate",   VOICE_RATE)
                engine.setProperty("volume", VOICE_VOLUME)
                engine.setProperty("voice",  VOICE_ID)
                engine.say(text)
                engine.runAndWait()
                engine.stop()
                return
            except Exception:
                if attempt == 0:
                    continue  # riprova una volta
