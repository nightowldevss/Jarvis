import json
import os
import queue
import socket
import threading
import numpy as np
import sounddevice as sd
import speech_recognition as sr
from vosk import Model, KaldiRecognizer
from config import LANGUAGE

SAMPLE_RATE  = 16000
BLOCK_SIZE   = 512
SILENCE_SECS = 1.2
MAX_SECS     = 12
MODEL_PATH   = os.path.join(os.path.dirname(__file__), "vosk-model-it")

_amplitude_callback = None
recognizer = sr.Recognizer()

# ── Carica modello vosk ────────────────────────────────────────────────────────
_vosk_model = None
def _get_vosk():
    global _vosk_model
    if _vosk_model is None and os.path.exists(MODEL_PATH):
        from vosk import SetLogLevel
        SetLogLevel(-1)   # silenzia log vosk
        _vosk_model = Model(MODEL_PATH)
    return _vosk_model

def set_amplitude_callback(fn):
    global _amplitude_callback
    _amplitude_callback = fn

def _is_online():
    try:
        socket.setdefaulttimeout(2)
        socket.create_connection(("8.8.8.8", 53))
        return True
    except OSError:
        return False

# ── Wake word offline con vosk ─────────────────────────────────────────────────
def wait_for_wake_word(wake_word="jarvis", timeout=None):
    """
    Ascolta in loop finché non sente la wake word.
    Usa vosk offline. Ritorna True quando la sente, False se timeout.
    """
    model = _get_vosk()
    if model is None:
        # fallback: usa Google (richiede internet)
        return _wait_wake_google(wake_word, timeout)

    rec   = KaldiRecognizer(model, SAMPLE_RATE)
    q     = queue.Queue()
    found = threading.Event()
    elapsed = [0]

    def callback(indata, frames, time_info, status):
        q.put(bytes(indata))
        if _amplitude_callback:
            _amplitude_callback(np.abs(np.frombuffer(bytes(indata), dtype=np.int16)).mean())

    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE,
                           dtype="int16", channels=1, callback=callback):
        while not found.is_set():
            try:
                data = q.get(timeout=0.5)
            except queue.Empty:
                elapsed[0] += 0.5
                if timeout and elapsed[0] >= timeout:
                    return False
                continue

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result()).get("text", "")
            else:
                result = json.loads(rec.PartialResult()).get("partial", "")

            if wake_word in result.lower():
                if _amplitude_callback:
                    _amplitude_callback(0)
                return True

            elapsed[0] += BLOCK_SIZE / SAMPLE_RATE
            if timeout and elapsed[0] >= timeout:
                return False

    return False


def _wait_wake_google(wake_word, timeout):
    """Fallback wake word via Google (online)."""
    import time
    start = time.time()
    while True:
        text = listen(timeout=5)
        if wake_word in text:
            return True
        if timeout and (time.time() - start) >= timeout:
            return False


# ── Ascolto comando (Google online, vosk offline come fallback) ────────────────
def listen(prompt=None, timeout=8):
    frames        = []
    silent_blocks = 0
    speaking      = False
    waited        = 0

    max_silent = int(SILENCE_SECS * SAMPLE_RATE / BLOCK_SIZE)
    max_blocks = int(MAX_SECS     * SAMPLE_RATE / BLOCK_SIZE)
    t_blocks   = int(timeout      * SAMPLE_RATE / BLOCK_SIZE)

    # Calibrazione rumore
    noise_samples = []
    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                            dtype="int16", blocksize=BLOCK_SIZE) as s:
            for _ in range(int(0.3 * SAMPLE_RATE / BLOCK_SIZE)):
                b, _ = s.read(BLOCK_SIZE)
                noise_samples.append(np.abs(b).mean())
    except Exception:
        return ""

    noise_floor = max(np.mean(noise_samples) * 2.5, 150) if noise_samples else 200

    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                            dtype="int16", blocksize=BLOCK_SIZE) as s:
            while waited < t_blocks:
                block, _ = s.read(BLOCK_SIZE)
                amp = np.abs(block).mean()
                if _amplitude_callback:
                    _amplitude_callback(amp)

                if not speaking:
                    if amp > noise_floor:
                        speaking = True
                        frames.append(block.copy())
                    else:
                        waited += 1
                else:
                    frames.append(block.copy())
                    if amp < noise_floor:
                        silent_blocks += 1
                        if silent_blocks >= max_silent:
                            break
                    else:
                        silent_blocks = 0
                    if len(frames) >= max_blocks:
                        break
    except Exception:
        return ""
    finally:
        if _amplitude_callback:
            _amplitude_callback(0)

    if not frames:
        return ""

    audio_data = sr.AudioData(np.concatenate(frames, axis=0).tobytes(), SAMPLE_RATE, 2)

    # Prova Google online
    if _is_online():
        try:
            return recognizer.recognize_google(audio_data, language=LANGUAGE).lower()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            pass  # fallback vosk

    # Fallback vosk offline
    return _recognize_vosk(np.concatenate(frames, axis=0))


def _recognize_vosk(audio_np):
    model = _get_vosk()
    if model is None:
        return "__offline__"
    rec = KaldiRecognizer(model, SAMPLE_RATE)
    rec.AcceptWaveform(audio_np.tobytes())
    result = json.loads(rec.FinalResult()).get("text", "")
    return result.lower() if result else ""
