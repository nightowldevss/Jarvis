"""
╔══════════════════════════════════════════════════════╗
║           J.A.R.V.I.S  —  Setup Installer           ║
╚══════════════════════════════════════════════════════╝
Esegui con: python setup.py
"""

import os
import sys
import subprocess
import shutil
import zipfile
import tempfile
import urllib.request
import winreg

APP_NAME    = "Jarvis"
APP_VERSION = "1.0.0"
INSTALL_DIR = os.path.join(os.environ.get("LOCALAPPDATA", "C:\\Users\\Public"), "Jarvis")
SOURCE_DIR  = os.path.dirname(os.path.abspath(__file__))
VOSK_URL    = "https://alphacephei.com/vosk/models/vosk-model-small-it-0.22.zip"
VOSK_DIR    = os.path.join(INSTALL_DIR, "vosk-model-it")
ICON_FILE   = os.path.join(SOURCE_DIR, "jarvis.ico")

REQUIREMENTS = [
    "speechrecognition", "pyttsx3", "sounddevice", "numpy", "vosk",
    "wikipedia-api", "requests", "beautifulsoup4", "psutil", "pyautogui",
    "pycaw", "keyboard", "pystray", "pillow", "deep-translator", "openai",
    "screen-brightness-control", "winshell", "pywin32", "packaging",
]

FILES_TO_COPY = [
    "gui.py", "main.py", "commands.py", "listener.py",
    "speaker.py", "memory.py", "config.py", "updater.py",
    "version.json", "jarvis.ico",
]

# ── Colori ─────────────────────────────────────────────────────────────────────
def _c(text, color):
    colors = {"green":"\033[92m","red":"\033[91m","yellow":"\033[93m",
              "cyan":"\033[96m","bold":"\033[1m","reset":"\033[0m"}
    return f"{colors.get(color,'')}{text}{colors['reset']}"

def step(msg):  print(f"\n{_c('>', 'cyan')} {_c(msg, 'bold')}")
def ok(msg):    print(f"  {_c('OK', 'green')} {msg}")
def warn(msg):  print(f"  {_c('!!', 'yellow')} {msg}")
def err(msg):   print(f"  {_c('ERR','red')} {msg}")

# ── Steps ──────────────────────────────────────────────────────────────────────
def check_python():
    step("Verifica Python")
    v = sys.version_info
    if v.major < 3 or v.minor < 9:
        err(f"Python 3.9+ richiesto. Attuale: {v.major}.{v.minor}")
        sys.exit(1)
    ok(f"Python {v.major}.{v.minor}.{v.micro}")

def create_dirs():
    step(f"Creazione cartella: {INSTALL_DIR}")
    os.makedirs(INSTALL_DIR, exist_ok=True)
    os.makedirs(os.path.join(INSTALL_DIR, "data"), exist_ok=True)
    ok("Cartelle create")

def install_deps():
    step("Installazione dipendenze")
    pip = [sys.executable, "-m", "pip", "install", "--quiet", "--upgrade"]
    for pkg in REQUIREMENTS:
        r = subprocess.run(pip + [pkg], capture_output=True)
        ok(pkg) if r.returncode == 0 else warn(f"{pkg} (possibile problema)")

def copy_files():
    step("Copia file applicazione")
    for f in FILES_TO_COPY:
        src = os.path.join(SOURCE_DIR, f)
        dst = os.path.join(INSTALL_DIR, f)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            ok(f)
        else:
            warn(f"Non trovato: {f}")

def copy_vosk():
    step("Copia modello Vosk")
    src = os.path.join(SOURCE_DIR, "vosk-model-it")
    if os.path.exists(src):
        if os.path.exists(VOSK_DIR):
            shutil.rmtree(VOSK_DIR)
        shutil.copytree(src, VOSK_DIR)
        ok("Modello Vosk copiato")
    else:
        warn("Modello non trovato, scarico...")
        _download_vosk()

def _download_vosk():
    if os.path.exists(VOSK_DIR):
        ok("Vosk gia' presente")
        return
    try:
        tmp = os.path.join(tempfile.gettempdir(), "vosk.zip")
        def prog(c, b, t):
            pct = min(100, int(c*b*100/max(t,1)))
            print(f"\r  Scaricando... {pct}%", end="", flush=True)
        urllib.request.urlretrieve(VOSK_URL, tmp, reporthook=prog)
        print()
        with zipfile.ZipFile(tmp, "r") as z:
            z.extractall(INSTALL_DIR)
        extracted = os.path.join(INSTALL_DIR, "vosk-model-small-it-0.22")
        if os.path.exists(extracted):
            os.rename(extracted, VOSK_DIR)
        os.remove(tmp)
        ok("Vosk installato")
    except Exception as e:
        warn(f"Download Vosk fallito: {e}")

def build_exe():
    """Compila gui.py in .exe con PyInstaller — protegge il codice sorgente."""
    step("Compilazione eseguibile (protegge il codice)")
    icon_arg = f"--icon={ICON_FILE}" if os.path.exists(ICON_FILE) else ""
    vosk_arg = f"--add-data={VOSK_DIR};vosk-model-it" if os.path.exists(VOSK_DIR) else ""

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",          # nessun terminale
        "--name", "Jarvis",
        f"--distpath={INSTALL_DIR}",
        f"--workpath={os.path.join(tempfile.gettempdir(), 'jarvis_build')}",
        f"--specpath={tempfile.gettempdir()}",
    ]
    if icon_arg: cmd.append(icon_arg)
    if vosk_arg: cmd.append(vosk_arg)

    # Aggiungi tutti i file dati necessari
    for f in ["config.py", "version.json", "jarvis.ico"]:
        src = os.path.join(INSTALL_DIR, f)
        if os.path.exists(src):
            cmd.append(f"--add-data={src};.")

    cmd.append(os.path.join(INSTALL_DIR, "gui.py"))

    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        ok("Eseguibile creato: Jarvis.exe")
        # Rimuovi i .py dall'installazione (codice protetto)
        for f in FILES_TO_COPY:
            if f.endswith(".py") and f not in ("config.py",):
                p = os.path.join(INSTALL_DIR, f)
                if os.path.exists(p):
                    os.remove(p)
        ok("File sorgente rimossi (codice protetto)")
    else:
        warn("Compilazione fallita, Jarvis funzionera' con i file .py")
        warn(r.stderr[-300:] if r.stderr else "")

def create_shortcut():
    step("Creazione collegamento Desktop con icona")
    try:
        import winshell
        desktop = winshell.desktop()
        lnk     = os.path.join(desktop, "Jarvis.lnk")
        exe     = os.path.join(INSTALL_DIR, "Jarvis.exe")
        # Se exe non esiste usa pythonw
        if not os.path.exists(exe):
            target = sys.executable.replace("python.exe", "pythonw.exe")
            args   = f'"{os.path.join(INSTALL_DIR, "gui.py")}"'
        else:
            target = exe
            args   = ""
        with winshell.shortcut(lnk) as s:
            s.path              = target
            s.arguments         = args
            s.working_directory = INSTALL_DIR
            s.description       = "J.A.R.V.I.S - Assistente Vocale"
            if os.path.exists(ICON_FILE):
                s.icon_location = (ICON_FILE, 0)
        ok(f"Collegamento con icona: {lnk}")
    except Exception as e:
        warn(f"Collegamento non creato: {e}")

def register():
    step("Registrazione in Aggiungi/Rimuovi programmi")
    try:
        exe = os.path.join(INSTALL_DIR, "Jarvis.exe")
        key = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Jarvis"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key) as k:
            winreg.SetValueEx(k, "DisplayName",     0, winreg.REG_SZ, "J.A.R.V.I.S Assistente Vocale")
            winreg.SetValueEx(k, "DisplayVersion",  0, winreg.REG_SZ, APP_VERSION)
            winreg.SetValueEx(k, "Publisher",       0, winreg.REG_SZ, "Jarvis Project")
            winreg.SetValueEx(k, "InstallLocation", 0, winreg.REG_SZ, INSTALL_DIR)
            winreg.SetValueEx(k, "DisplayIcon",     0, winreg.REG_SZ, ICON_FILE if os.path.exists(ICON_FILE) else "")
            winreg.SetValueEx(k, "UninstallString", 0, winreg.REG_SZ,
                              f'"{sys.executable}" "{os.path.join(INSTALL_DIR, "uninstall.py")}"')
            winreg.SetValueEx(k, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(k, "NoRepair", 0, winreg.REG_DWORD, 1)
        ok("Registrato")
    except Exception as e:
        warn(f"Registrazione fallita: {e}")

def create_uninstaller():
    step("Creazione uninstaller")
    code = f'''import os, shutil, winreg
INSTALL_DIR = r"{INSTALL_DIR}"
import ctypes
if ctypes.windll.user32.MessageBoxW(0,"Vuoi disinstallare Jarvis?","Disinstalla",4) != 6:
    exit()
try:
    import winshell
    lnk = os.path.join(winshell.desktop(), "Jarvis.lnk")
    if os.path.exists(lnk): os.remove(lnk)
except: pass
try:
    winreg.DeleteKey(winreg.HKEY_CURRENT_USER,
        r"Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\Jarvis")
except: pass
shutil.rmtree(INSTALL_DIR, ignore_errors=True)
ctypes.windll.user32.MessageBoxW(0,"Jarvis disinstallato.","OK",0)
'''
    with open(os.path.join(INSTALL_DIR, "uninstall.py"), "w", encoding="utf-8") as f:
        f.write(code)
    ok("Uninstaller creato")

def print_done():
    print(f"""
{'='*54}
  Jarvis installato correttamente!
{'='*54}
  Cartella : {INSTALL_DIR}
  Desktop  : Doppio click su "Jarvis"
  Hotkey   : Ctrl+Shift+J
  Config   : {os.path.join(INSTALL_DIR, 'config.py')}
{'='*54}
""")

# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.system("cls")
    print(_c("""
  ╔══════════════════════════════════════════════════╗
  ║        J.A.R.V.I.S  —  Installer v1.0           ║
  ╚══════════════════════════════════════════════════╝
""", "cyan"))
    print(f"  Destinazione: {_c(INSTALL_DIR, 'yellow')}")
    input(f"\n  Premi INVIO per iniziare o CTRL+C per annullare...")

    check_python()
    create_dirs()
    install_deps()
    copy_files()
    copy_vosk()
    build_exe()
    create_shortcut()
    register()
    create_uninstaller()
    print_done()
    input("  Premi INVIO per chiudere...")
