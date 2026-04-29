"""
Esegui questo script per generare Jarvis-Setup.exe
Richiede NSIS installato: https://nsis.sourceforge.io/Download
"""
import os
import sys
import py_compile
import subprocess
import shutil

SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))

NSIS_PATHS = [
    r"C:\Program Files (x86)\NSIS\makensis.exe",
    r"C:\Program Files\NSIS\makensis.exe",
]

FILES_TO_COMPILE = [
    "gui", "commands", "listener",
    "speaker", "memory", "updater", "main",
]

def compile_pyc():
    print("\n> Compilazione file .pyc...")
    for name in FILES_TO_COMPILE:
        src = os.path.join(SOURCE_DIR, f"{name}.py")
        dst = os.path.join(SOURCE_DIR, f"{name}.pyc")
        if os.path.exists(src):
            py_compile.compile(src, cfile=dst, optimize=2)
            print(f"  OK {name}.py -> {name}.pyc")
        else:
            print(f"  !! {name}.py non trovato")

def build_installer():
    print("\n> Creazione Jarvis-Setup.exe con NSIS...")
    nsis = None
    for path in NSIS_PATHS:
        if os.path.exists(path):
            nsis = path
            break

    if not nsis:
        print("  ERR NSIS non trovato!")
        print("  Scaricalo da: https://nsis.sourceforge.io/Download")
        return False

    nsi = os.path.join(SOURCE_DIR, "installer.nsi")
    r = subprocess.run([nsis, nsi], capture_output=True, text=True, cwd=SOURCE_DIR)

    if r.returncode == 0:
        print("  OK Jarvis-Setup.exe creato!")
        return True
    else:
        print("  ERR Errore NSIS:")
        print(r.stdout[-500:])
        return False

def cleanup_pyc():
    """Rimuove i .pyc temporanei dalla cartella sorgente."""
    for name in FILES_TO_COMPILE:
        dst = os.path.join(SOURCE_DIR, f"{name}.pyc")
        if os.path.exists(dst):
            os.remove(dst)

if __name__ == "__main__":
    print("""
  ╔══════════════════════════════════════════════════╗
  ║      J.A.R.V.I.S  —  Build Installer            ║
  ╚══════════════════════════════════════════════════╝
""")
    compile_pyc()
    ok = build_installer()
    cleanup_pyc()

    if ok:
        out = os.path.join(SOURCE_DIR, "Jarvis-Setup.exe")
        size = round(os.path.getsize(out) / 1024 / 1024, 1)
        print(f"""
  Fatto! File creato:
  {out} ({size} MB)

  Caricalo su GitHub Releases come asset della release.
""")
    input("  Premi INVIO per chiudere...")
