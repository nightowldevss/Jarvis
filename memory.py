import json
import os
import datetime

DATA_DIR     = os.path.join(os.path.dirname(__file__), "data")
PROFILE_FILE = os.path.join(DATA_DIR, "profile.json")
LOG_FILE     = os.path.join(DATA_DIR, "history.log")
MEMORY_FILE  = os.path.join(DATA_DIR, "memory.json")

os.makedirs(DATA_DIR, exist_ok=True)

# ── Profilo utente ─────────────────────────────────────────────────────────────
_DEFAULT_PROFILE = {
    "name":       "Utente",
    "hotkey":     "ctrl+shift+j",
    "theme":      "dark",
    "voice_rate": 155,
    "wake_word":  "jarvis",
    "reminders":  [],
}

def load_profile():
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                p = json.load(f)
                # merge con default per campi mancanti
                for k, v in _DEFAULT_PROFILE.items():
                    p.setdefault(k, v)
                return p
        except Exception:
            pass
    return dict(_DEFAULT_PROFILE)

def save_profile(profile):
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

# ── Memoria conversazione ──────────────────────────────────────────────────────
_MAX_MEMORY = 20   # ultimi N scambi ricordati

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory[-_MAX_MEMORY:], f, ensure_ascii=False, indent=2)

def add_to_memory(role, text):
    """role: 'user' | 'jarvis'"""
    memory = load_memory()
    memory.append({
        "role": role,
        "text": text,
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_memory(memory)

def get_last_context(n=5):
    """Ritorna gli ultimi n scambi come stringa leggibile."""
    memory = load_memory()
    lines = []
    for m in memory[-n:]:
        prefix = "Tu" if m["role"] == "user" else "Jarvis"
        lines.append(f"{prefix}: {m['text']}")
    return "\n".join(lines)

# ── Log su file ────────────────────────────────────────────────────────────────
def log_to_file(role, text):
    """Scrive ogni scambio nel file di log con timestamp."""
    ts     = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = "TU    " if role == "user" else "JARVIS"
    line   = f"[{ts}] {prefix} > {text}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)

def get_log_path():
    return LOG_FILE
