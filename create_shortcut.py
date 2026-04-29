import winshell
import os
import sys

desktop = winshell.desktop()
shortcut_path = os.path.join(desktop, "Jarvis.lnk")

python_exe = sys.executable.replace("python.exe", "pythonw.exe")
script = r"c:\xampp\htdocs\Jarvis\gui.py"
working_dir = r"c:\xampp\htdocs\Jarvis"

with winshell.shortcut(shortcut_path) as s:
    s.path = python_exe
    s.arguments = f'"{script}"'
    s.working_directory = working_dir
    s.description = "Avvia Jarvis"

print(f"Collegamento creato: {shortcut_path}")
