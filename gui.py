import tkinter as tk
from tkinter import ttk
import threading
import math
import datetime
import time
import keyboard
import pystray
import sys
import os
import tempfile
from PIL import Image, ImageDraw
from listener import listen, wait_for_wake_word, set_amplitude_callback
from speaker import speak, set_log_callback as speaker_set_log
from commands import execute, set_shutdown_callback, set_log_callback as cmd_set_log
from memory import load_profile, save_profile, add_to_memory, log_to_file, get_log_path
from config import WAKE_WORD
from updater import check_for_updates, set_notify_callback, download_and_install, get_current_version

HOTKEY_DEFAULT = "ctrl+shift+j"

# ── Istanza singola ────────────────────────────────────────────────────────────
LOCK_FILE = os.path.join(tempfile.gettempdir(), "jarvis.lock")

def _check_single_instance():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                pid = int(f.read().strip())
            # Controlla se il processo è ancora attivo
            import psutil
            if psutil.pid_exists(pid):
                import ctypes
                ctypes.windll.user32.MessageBoxW(
                    0,
                    "Jarvis e' gia' in esecuzione in background.\nClicca sull'icona nella barra delle applicazioni per riaprirlo.",
                    "J.A.R.V.I.S - Gia' attivo",
                    0x40
                )
                sys.exit(0)
            else:
                # Processo morto (PC spento di forza) — rimuovi il lock fantasma
                os.remove(LOCK_FILE)
        except Exception:
            # Lock corrotto o illeggibile — rimuovilo
            try: os.remove(LOCK_FILE)
            except Exception: pass
    # Crea il file di lock con il PID attuale
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

def _remove_lock():
    try:
        os.remove(LOCK_FILE)
    except Exception:
        pass

_check_single_instance()

# ── Stato ──────────────────────────────────────────────────────────────────────
active = False
jarvis_thread = None
current_amplitude = 0.0
_state = "offline"
_toggle_lock = threading.Lock()  # FIX: evita doppio Jarvis

# ── Temi ───────────────────────────────────────────────────────────────────────
THEMES = {
    "dark": {
        "bg":             "#07080f",
        "panel":          "#0d0f1e",
        "border":         "#1a2a3a",
        "cyan":           "#00d4ff",
        "green":          "#00ff88",
        "red":            "#ff4455",
        "orange":         "#ffaa00",
        "white":          "#e0f0ff",
        "dim":            "#2a3a4a",
        "chat_bg":        "#0a0c18",
        "user_bubble":    "#0d2a3a",
        "jarvis_bubble":  "#0a1a0a",
        "text":           "#e0f0ff",
    },
    "light": {
        "bg":             "#f0f4f8",
        "panel":          "#dce8f0",
        "border":         "#a0b8cc",
        "cyan":           "#0077aa",
        "green":          "#007744",
        "red":            "#cc2233",
        "orange":         "#cc7700",
        "white":          "#111122",
        "dim":            "#889aaa",
        "chat_bg":        "#e8f0f8",
        "user_bubble":    "#c8dff0",
        "jarvis_bubble":  "#d0f0e0",
        "text":           "#111122",
    }
}
current_theme = "dark"
C = dict(THEMES[current_theme])

# ── Finestra principale ────────────────────────────────────────────────────────
root = tk.Tk()
root.title("J.A.R.V.I.S")
root.geometry("520x800")
root.configure(bg=C["bg"])
root.resizable(True, True)
root.minsize(420, 600)
root.attributes("-topmost", True)
root.overrideredirect(True)

_drag_x = _drag_y = 0
_pinned = True

def start_drag(e): global _drag_x, _drag_y; _drag_x, _drag_y = e.x, e.y
def do_drag(e): root.geometry(f"+{root.winfo_x()+e.x-_drag_x}+{root.winfo_y()+e.y-_drag_y}")

def on_close():
    global active
    active = False
    try: keyboard.unhook_all()
    except Exception: pass
    _remove_lock()
    tray_icon.stop()
    root.destroy()

def show_window():
    root.after(0, root.deiconify)
    root.after(0, lambda: root.attributes("-topmost", _pinned))

def hide_window():
    root.withdraw()
    tray_icon.notify("Jarvis", "In esecuzione in background. Clicca sull'icona per riaprire.")

# ── System Tray ───────────────────────────────────────────────────────────────
def _make_tray_icon():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([4, 4, 60, 60], fill=(0, 212, 255, 255))
    d.ellipse([16, 16, 48, 48], fill=(7, 8, 15, 255))
    d.ellipse([24, 24, 40, 40], fill=(0, 212, 255, 200))
    return img

tray_menu = pystray.Menu(
    pystray.MenuItem("Mostra Jarvis", lambda: show_window(), default=True),
    pystray.MenuItem("Attiva / Disattiva", lambda: root.after(0, toggle)),
    pystray.MenuItem("Impostazioni profilo", lambda: root.after(0, open_profile_settings)),
    pystray.MenuItem("Apri log conversazioni", lambda: root.after(0, open_log)),
    pystray.Menu.SEPARATOR,
    pystray.MenuItem("Chiudi", lambda: root.after(0, on_close)),
)
tray_icon = pystray.Icon("Jarvis", _make_tray_icon(), "J.A.R.V.I.S", tray_menu)
threading.Thread(target=tray_icon.run, daemon=True).start()

# ── Barra titolo custom ────────────────────────────────────────────────────────
title_bar = tk.Frame(root, bg=C["panel"], height=38)
title_bar.pack(fill="x")
title_bar.pack_propagate(False)
title_bar.bind("<ButtonPress-1>", start_drag)
title_bar.bind("<B1-Motion>", do_drag)

tk.Label(title_bar, text="  J.A.R.V.I.S",
         font=("Courier New", 10, "bold"), fg=C["cyan"], bg=C["panel"]).pack(side="left", pady=8)
tk.Label(title_bar, text="Assistente Vocale",
         font=("Courier New", 7), fg=C["dim"], bg=C["panel"]).pack(side="left", padx=4, pady=8)

for txt, cmd, fg in [
    ("X", hide_window, C["dim"]),
    ("Q", on_close,   C["red"]),
]:
    tk.Button(title_bar, text=f"  {txt}  ", font=("Courier New", 9, "bold"),
              fg=fg, bg=C["panel"], bd=0, cursor="hand2",
              activebackground=fg, activeforeground=C["bg"],
              command=cmd).pack(side="right", padx=2)

# Pulsante profilo
_profile_btn = tk.Button(title_bar, text=" U ", font=("Courier New", 9, "bold"),
          fg=C["green"], bg=C["panel"], bd=0, cursor="hand2",
          activebackground=C["green"], activeforeground=C["bg"])
_profile_btn.pack(side="right", padx=2)

# Pulsante tema
theme_btn = tk.Button(title_bar, text=" D ", font=("Courier New", 9, "bold"),
                      fg=C["orange"], bg=C["panel"], bd=0, cursor="hand2",
                      activebackground=C["orange"], activeforeground=C["bg"])
theme_btn.pack(side="right", padx=2)

# Pulsante pin
pin_btn = tk.Button(title_bar, text=" P ", font=("Courier New", 9, "bold"),
                    fg=C["cyan"], bg=C["panel"], bd=0, cursor="hand2",
                    activebackground=C["cyan"], activeforeground=C["bg"])
pin_btn.pack(side="right", padx=2)

def toggle_pin():
    global _pinned
    _pinned = not _pinned
    root.attributes("-topmost", _pinned)
    pin_btn.config(fg=C["cyan"] if _pinned else C["dim"])
pin_btn.config(command=toggle_pin)

def toggle_theme():
    global current_theme, C
    current_theme = "light" if current_theme == "dark" else "dark"
    C = dict(THEMES[current_theme])
    theme_btn.config(text=" D " if current_theme == "dark" else " L ")
    _apply_theme()
theme_btn.config(command=toggle_theme)

def _apply_theme():
    root.configure(bg=C["bg"])
    for w in [header, btn_frame, log_frame]:
        try: w.configure(bg=C["bg"])
        except Exception: pass
    title_bar.configure(bg=C["panel"])
    chat_frame.configure(bg=C["chat_bg"])
    chat_inner.configure(bg=C["chat_bg"])
    chat_canvas.configure(bg=C["chat_bg"])
    canvas.configure(bg=C["bg"])
    bars_canvas.configure(bg=C["bg"])
    clock_label.configure(fg=C["cyan"], bg=C["bg"])
    date_label.configure(fg=C["dim"], bg=C["bg"])
    status_label.configure(bg=C["bg"])

# ── Separatore ────────────────────────────────────────────────────────────────
tk.Frame(root, bg=C["cyan"], height=1).pack(fill="x")

# ── Header ────────────────────────────────────────────────────────────────────
header = tk.Frame(root, bg=C["bg"])
header.pack(fill="x", padx=20, pady=(8, 0))

clock_label = tk.Label(header, text="00:00:00", font=("Courier New", 13, "bold"),
                       fg=C["cyan"], bg=C["bg"])
clock_label.pack(side="left")

date_label = tk.Label(header, text="", font=("Courier New", 8),
                      fg=C["dim"], bg=C["bg"])
date_label.pack(side="left", padx=10)

status_label = tk.Label(header, text="[ OFFLINE ]", font=("Courier New", 10, "bold"),
                        fg=C["red"], bg=C["bg"])
status_label.pack(side="right")

def update_clock():
    now = datetime.datetime.now()
    clock_label.config(text=now.strftime("%H:%M:%S"))
    giorni = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
    date_label.config(text=f"{giorni[now.weekday()]} {now.strftime('%d/%m/%Y')}")
    root.after(1000, update_clock)
update_clock()

# ── Canvas sfera ──────────────────────────────────────────────────────────────
canvas = tk.Canvas(root, width=520, height=200, bg=C["bg"], highlightthickness=0)
canvas.pack(fill="x")

# ── Barre audio ───────────────────────────────────────────────────────────────
bars_canvas = tk.Canvas(root, width=520, height=36, bg=C["bg"], highlightthickness=0)
bars_canvas.pack(fill="x")

# ── Chat ──────────────────────────────────────────────────────────────────────
tk.Frame(root, bg=C["border"], height=1).pack(fill="x", padx=16)

chat_frame = tk.Frame(root, bg=C["chat_bg"])
chat_frame.pack(fill="both", expand=True, padx=10, pady=6)

chat_canvas = tk.Canvas(chat_frame, bg=C["chat_bg"], highlightthickness=0)
scrollbar = tk.Scrollbar(chat_frame, orient="vertical", command=chat_canvas.yview,
                         width=5, troughcolor=C["bg"])
chat_canvas.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
chat_canvas.pack(side="left", fill="both", expand=True)

chat_inner = tk.Frame(chat_canvas, bg=C["chat_bg"])
chat_window = chat_canvas.create_window((0, 0), window=chat_inner, anchor="nw")

chat_canvas.bind("<Configure>", lambda e: chat_canvas.itemconfig(chat_window, width=e.width))
chat_inner.bind("<Configure>", lambda e: chat_canvas.configure(scrollregion=chat_canvas.bbox("all")))

# ── Pulsante + hotkey ─────────────────────────────────────────────────────────
tk.Frame(root, bg=C["border"], height=1).pack(fill="x", padx=16)

log_frame = tk.Frame(root, bg=C["bg"])
log_frame.pack(fill="x", pady=10)

btn_frame = tk.Frame(log_frame, bg=C["bg"])
btn_frame.pack()

btn = tk.Button(btn_frame, text="  ATTIVA JARVIS  ",
                font=("Courier New", 11, "bold"),
                bg=C["dim"], fg=C["cyan"], bd=0, cursor="hand2",
                padx=20, pady=8,
                activebackground=C["cyan"], activeforeground=C["bg"])
btn.pack()

hotkey_label = tk.Label(btn_frame, text=f"Hotkey: {HOTKEY_DEFAULT}",
                        font=("Courier New", 8), fg=C["dim"], bg=C["bg"])
hotkey_label.pack(pady=(4, 0))

tk.Button(btn_frame, text="Cambia tasto rapido", font=("Courier New", 8),
          fg=C["dim"], bg=C["bg"], bd=0, cursor="hand2",
          activeforeground=C["cyan"], activebackground=C["bg"],
          command=lambda: open_hotkey_settings()).pack(pady=(2, 0))

# ── Animazione sfera ──────────────────────────────────────────────────────────
_angle = 0.0
_pulse = 0.0
_wave_offset = 0.0

def _blend(c1, c2, t):
    r1,g1,b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
    r2,g2,b2 = int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16)
    r = max(0, min(255, int(r1*t+r2*(1-t))))
    g = max(0, min(255, int(g1*t+g2*(1-t))))
    b = max(0, min(255, int(b1*t+b2*(1-t))))
    return f"#{r:02x}{g:02x}{b:02x}"

def draw_sphere():
    global _angle, _pulse, _wave_offset
    canvas.delete("all")
    w = canvas.winfo_width() or 520
    cx, cy, r = w // 2, 100, 68

    if _state == "speaking":   base, glow = C["green"],  C["green"]
    elif _state == "listening": base, glow = C["orange"], C["orange"]
    elif _state == "thinking":  base, glow = C["cyan"],   C["cyan"]
    else:                       base, glow = "#1a2a3a",   "#0d1a22"

    pr = r + 12 + math.sin(_pulse) * 5
    for i in range(7, 0, -1):
        col = _blend(glow, C["bg"], i / 8)
        d = i * 5
        canvas.create_oval(cx-pr-d, cy-pr-d, cx+pr+d, cy+pr+d, outline=col, width=1)

    for i in range(28, 0, -1):
        t = i / 28
        col = _blend(base, C["bg"], t * 0.88)
        off = int((1 - t) * r * 0.42)
        canvas.create_oval(cx-r+off, cy-r+off, cx+r-off, cy+r-off, fill=col, outline="")

    for i, offset in enumerate([0, 60, 120]):
        a = math.radians(_angle + offset)
        rx = int(r * 1.32 * abs(math.cos(a)))
        ry = int(r * 0.27)
        tilt = int(i * 7 * math.sin(math.radians(_angle)))
        col = _blend(base, C["bg"], 0.65) if active else C["dim"]
        canvas.create_oval(cx-rx, cy-ry+tilt, cx+rx, cy+ry+tilt,
                           outline=col, width=2 if active else 1)

    if active:
        for i in range(6):
            pa = math.radians(_angle * 1.5 + i * 60)
            px = cx + int((r + 16) * math.cos(pa))
            py = cy + int((r * 0.38) * math.sin(pa))
            sz = 3 if i % 2 == 0 else 2
            canvas.create_oval(px-sz, py-sz, px+sz, py+sz, fill=base, outline="")

    canvas.create_oval(cx-r//3-2, cy-r//2-2, cx-r//8, cy-r//3,
                       fill="#ffffff", outline="", stipple="gray50")

    if _state in ("listening", "speaking") and current_amplitude > 50:
        amp = min(current_amplitude / 3000, 1.0) * 22
        for i in range(1, 5):
            wr = r + 18 + i * 13 + math.sin(_wave_offset + i) * amp
            col = _blend(base, C["bg"], max(0, 1 - i * 0.23))
            canvas.create_oval(cx-wr, cy-wr*0.48, cx+wr, cy+wr*0.48, outline=col, width=1)

    _angle = (_angle + (1.8 if active else 0.2)) % 360
    _pulse += 0.07 if active else 0.02
    _wave_offset += 0.14
    root.after(28, draw_sphere)

# ── Barre audio ───────────────────────────────────────────────────────────────
_bar_phases = [i * 0.4 for i in range(26)]

def draw_bars():
    bars_canvas.delete("all")
    w = bars_canvas.winfo_width() or 520
    h = 36
    n = 26
    bar_w = 7
    gap = max(1, (w - n * bar_w) // (n + 1))

    for i in range(n):
        x = gap + i * (bar_w + gap)
        if active and current_amplitude > 80:
            af = min(current_amplitude / 4000, 1.0)
            bh = int(3 + math.sin(_bar_phases[i]) * 13 * af + af * 9)
        elif active:
            bh = int(2 + math.sin(_bar_phases[i]) * 2.5)
        else:
            bh = 2

        col = _blend(C["cyan"], C["green"], i / n) if active else C["dim"]
        bars_canvas.create_rectangle(x, h//2-bh, x+bar_w, h//2+bh, fill=col, outline="")
        _bar_phases[i] += 0.17 if active else 0.03

    root.after(38, draw_bars)

# ── Chat ──────────────────────────────────────────────────────────────────────
def add_message(text, sender="jarvis"):
    color  = C["cyan"]   if sender == "jarvis" else C["orange"]
    bg     = C["jarvis_bubble"] if sender == "jarvis" else C["user_bubble"]
    anchor = "w"  if sender == "jarvis" else "e"
    prefix = "J >" if sender == "jarvis" else "Tu>"
    padx   = (8, 50) if sender == "jarvis" else (50, 8)

    row = tk.Frame(chat_inner, bg=C["chat_bg"])
    row.pack(fill="x", pady=2, padx=4)

    bubble = tk.Frame(row, bg=bg, padx=10, pady=5)
    bubble.pack(anchor=anchor, padx=padx)

    tk.Label(bubble, text=prefix, font=("Courier New", 7, "bold"),
             fg=color, bg=bg).pack(anchor="w")
    tk.Label(bubble, text=text, font=("Courier New", 9),
             fg=C["text"], bg=bg, wraplength=280, justify="left").pack(anchor="w")

    chat_canvas.update_idletasks()
    chat_canvas.yview_moveto(1.0)

def on_log(text, sender):
    add_to_memory(sender, text)
    log_to_file(sender, text)
    root.after(0, lambda: add_message(text, sender))

# ── Stato ─────────────────────────────────────────────────────────────────────
def set_state(state, label, color):
    global _state
    _state = state
    root.after(0, lambda: status_label.config(text=f"[ {label} ]", fg=color))

# ── Profilo ───────────────────────────────────────────────────────────────────
profile = load_profile()

# ── Loop Jarvis ───────────────────────────────────────────────────────────────
def jarvis_loop():
    speak(f"Ciao {profile['name']}! Jarvis attivo. Dimmi pure!")
    while active:
        set_state("listening", "IN ASCOLTO", C["orange"])

        # Wake word offline con vosk
        heard = wait_for_wake_word(wake_word=profile.get("wake_word", WAKE_WORD), timeout=10)
        if not active:
            break
        if not heard:
            continue

        # Ascolta il comando
        set_state("listening", "IN ATTESA", C["orange"])
        speak("Dimmi!")
        command = listen(timeout=8)

        if not active:
            break
        if not command or command == "__offline__":
            if command == "__offline__":
                set_state("offline", "NO RETE", C["red"])
                speak("Nessuna connessione a internet.")
                time.sleep(3)
            else:
                speak("Non ho sentito nulla.")
            continue

        # Salva in memoria e log
        add_to_memory("user", command)
        log_to_file("user", command)

        set_state("thinking", "ELABORO", C["cyan"])
        execute(command)

    set_state("offline", "OFFLINE", C["red"])

# ── Toggle (con lock per evitare doppio Jarvis) ───────────────────────────────
def toggle():
    global active, jarvis_thread
    if not _toggle_lock.acquire(blocking=False):
        return  # già in esecuzione, ignora
    try:
        if not active:
            active = True
            btn.config(text="  DISATTIVA JARVIS  ", bg="#002200", fg=C["green"])
            set_state("listening", "ONLINE", C["green"])
            add_message("Sistema avviato. In ascolto...", "jarvis")
            jarvis_thread = threading.Thread(target=jarvis_loop, daemon=True)
            jarvis_thread.start()
        else:
            active = False
            btn.config(text="  ATTIVA JARVIS  ", bg=C["dim"], fg=C["cyan"])
            set_state("offline", "OFFLINE", C["red"])
            speak("Jarvis in standby.")
    finally:
        _toggle_lock.release()

btn.config(command=toggle)

# ── Hotkey ────────────────────────────────────────────────────────────────────
current_hotkey = HOTKEY_DEFAULT

def register_hotkey(hk):
    global current_hotkey
    try: keyboard.remove_hotkey(current_hotkey)
    except Exception: pass
    current_hotkey = hk
    keyboard.add_hotkey(hk, lambda: root.after(0, toggle))

def open_hotkey_settings():
    win = tk.Toplevel(root)
    win.title("Tasto rapido")
    win.geometry("320x170")
    win.configure(bg=C["panel"])
    win.resizable(False, False)
    win.attributes("-topmost", True)

    tk.Label(win, text="Inserisci la combinazione di tasti:",
             font=("Courier New", 9), fg=C["dim"], bg=C["panel"]).pack(pady=(16, 4))

    entry_var = tk.StringVar(value=current_hotkey)
    entry = tk.Entry(win, textvariable=entry_var, font=("Courier New", 11, "bold"),
                     fg=C["cyan"], bg=C["bg"], insertbackground=C["cyan"],
                     bd=0, justify="center")
    entry.pack(padx=30, fill="x")

    msg = tk.Label(win, text="", font=("Courier New", 8), fg=C["green"], bg=C["panel"])
    msg.pack(pady=6)

    def save():
        hk = entry_var.get().strip()
        if not hk: return
        try:
            register_hotkey(hk)
            hotkey_label.config(text=f"Hotkey: {hk}")
            msg.config(text=f"Salvato! Usa '{hk}' per attivare.", fg=C["green"])
        except Exception as e:
            msg.config(text=f"Tasto non valido.", fg=C["red"])

    tk.Button(win, text="SALVA", font=("Courier New", 10, "bold"),
              fg=C["bg"], bg=C["cyan"], bd=0, padx=16, pady=6,
              cursor="hand2", command=save).pack()

register_hotkey(HOTKEY_DEFAULT)

# ── Profilo settings ────────────────────────────────────────────────────────────
def open_profile_settings():
    win = tk.Toplevel(root)
    win.title("Profilo")
    win.geometry("340x260")
    win.configure(bg=C["panel"])
    win.resizable(False, False)
    win.attributes("-topmost", True)

    fields = [
        ("Nome",       "name"),
        ("Wake word",  "wake_word"),
    ]
    entries = {}
    for label, key in fields:
        tk.Label(win, text=label, font=("Courier New", 9),
                 fg=C["dim"], bg=C["panel"]).pack(pady=(12, 2))
        var = tk.StringVar(value=profile.get(key, ""))
        e = tk.Entry(win, textvariable=var, font=("Courier New", 10),
                     fg=C["cyan"], bg=C["bg"], insertbackground=C["cyan"],
                     bd=0, justify="center")
        e.pack(padx=30, fill="x")
        entries[key] = var

    msg = tk.Label(win, text="", font=("Courier New", 8), fg=C["green"], bg=C["panel"])
    msg.pack(pady=6)

    def save():
        for key, var in entries.items():
            profile[key] = var.get().strip()
        save_profile(profile)
        msg.config(text="Profilo salvato!", fg=C["green"])

    tk.Button(win, text="SALVA", font=("Courier New", 10, "bold"),
              fg=C["bg"], bg=C["cyan"], bd=0, padx=16, pady=6,
              cursor="hand2", command=save).pack()


def open_log():
    import subprocess as sp
    path = get_log_path()
    if os.path.exists(path):
        sp.Popen(["notepad.exe", path])
    else:
        speak("Nessun log disponibile ancora.")

# Collega il pulsante profilo ora che la funzione esiste
_profile_btn.config(command=open_profile_settings)


# ── Callback ──────────────────────────────────────────────────────────────────
def on_amplitude(amp):
    global current_amplitude
    current_amplitude = amp

set_amplitude_callback(on_amplitude)
speaker_set_log(on_log)
cmd_set_log(on_log)
set_shutdown_callback(lambda: root.after(0, toggle))

# ── Avvio ─────────────────────────────────────────────────────────────────────
add_message("Sistema inizializzato. Premi ATTIVA per iniziare.", "jarvis")
draw_sphere()
draw_bars()
root.mainloop()
