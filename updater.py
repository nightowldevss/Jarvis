import json
import os
import sys
import threading
import subprocess
import tempfile
import urllib.request
from packaging.version import Version

# URL del file version.json sul tuo server — cambia con il tuo URL reale
VERSION_URL  = "https://tuosito.com/jarvis/version.json"
CURRENT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "version.json")

_notify_callback = None   # GUI chiama questo per mostrare il popup

def set_notify_callback(fn):
    global _notify_callback
    _notify_callback = fn

def get_current_version():
    try:
        with open(CURRENT_FILE, "r") as f:
            return json.load(f).get("version", "0.0.0")
    except Exception:
        return "0.0.0"

def check_for_updates():
    """Controlla aggiornamenti in background. Non blocca l'avvio."""
    threading.Thread(target=_check, daemon=True).start()

def _check():
    try:
        with urllib.request.urlopen(VERSION_URL, timeout=5) as r:
            remote = json.loads(r.read().decode())
    except Exception:
        return  # nessuna rete o server non raggiungibile, ignora silenziosamente

    remote_ver  = remote.get("version", "0.0.0")
    current_ver = get_current_version()

    if Version(remote_ver) > Version(current_ver):
        notes = remote.get("notes", "")
        url   = remote.get("url", "")
        if _notify_callback:
            _notify_callback(remote_ver, notes, url)

def download_and_install(url, new_version):
    """Scarica il nuovo installer ed eseguilo."""
    try:
        tmp = os.path.join(tempfile.gettempdir(), "Jarvis-Setup.exe")

        def progress(count, block, total):
            if _notify_callback:
                pct = min(100, int(count * block * 100 / max(total, 1)))
                # aggiorna la GUI con la percentuale
                pass

        urllib.request.urlretrieve(url, tmp, reporthook=progress)

        # Aggiorna version.json locale
        with open(CURRENT_FILE, "r") as f:
            data = json.load(f)
        data["version"] = new_version
        with open(CURRENT_FILE, "w") as f:
            json.dump(data, f, indent=2)

        # Avvia il nuovo installer e chiudi Jarvis
        subprocess.Popen([tmp], shell=True)
        sys.exit(0)

    except Exception as e:
        if _notify_callback:
            _notify_callback(None, f"Errore download: {e}", None)
