import webbrowser
import subprocess
import datetime
import os
import re
import threading
import time
import socket
import wikipediaapi
import requests
import psutil
import pyautogui
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from bs4 import BeautifulSoup
from speaker import speak

wiki = wikipediaapi.Wikipedia(language="it", user_agent="Jarvis/1.0")

_shutdown_callback = None
_log_callback      = None
_reminders         = []

def set_shutdown_callback(fn):
    global _shutdown_callback
    _shutdown_callback = fn

def set_log_callback(fn):
    global _log_callback
    _log_callback = fn

def _log(msg):
    if _log_callback:
        _log_callback(msg, "user")

# ── Rete ───────────────────────────────────────────────────────────────────────
def _is_online():
    try:
        socket.setdefaulttimeout(2)
        socket.create_connection(("8.8.8.8", 53))
        return True
    except OSError:
        return False

def _require_network():
    """Ritorna True se c'è rete, altrimenti parla e ritorna False."""
    if not _is_online():
        speak("Non ho connessione a internet. Riprova più tardi.")
        return False
    return True

# ── Volume ─────────────────────────────────────────────────────────────────────
def _get_vol_interface():
    try:
        devices   = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    except Exception:
        return None

def _set_volume(pct):
    v = _get_vol_interface()
    if v:
        v.SetMasterVolumeLevelScalar(max(0.0, min(1.0, pct / 100)), None)

def _get_volume():
    v = _get_vol_interface()
    return int(v.GetMasterVolumeLevelScalar() * 100) if v else -1

# ── Sinonimi ───────────────────────────────────────────────────────────────────
# Ogni gruppo: se UNA delle parole è nel comando → match
_SYNONYMS = {
    "stop":          ["disattivati", "spegniti", "vai in standby", "stop", "fermati", "silenzio"],
    "musica_play":   ["metti", "riproduci", "ascolta", "suona", "fai partire", "manda"],
    "media_pause":   ["pausa", "metti in pausa", "stop musica", "ferma la musica"],
    "media_resume":  ["riprendi", "continua", "play", "continua la musica", "fai ripartire"],
    "media_next":    ["canzone successiva", "prossima canzone", "avanti", "salta", "prossima"],
    "media_prev":    ["canzone precedente", "torna indietro", "precedente", "indietro"],
    "vol_up":        ["alza", "aumenta", "alza il volume", "aumenta il volume", "più forte"],
    "vol_down":      ["abbassa", "diminuisci", "abbassa il volume", "più basso", "meno forte"],
    "vol_mute":      ["muto", "silenzia", "togli audio", "azzera volume"],
    "vol_query":     ["che volume", "quanto volume", "volume attuale"],
    "sveglia":       ["sveglia", "svegliami", "imposta sveglia", "metti sveglia"],
    "promemoria":    ["ricordami", "promemoria", "non dimenticare"],
    "ora":           ["che ore sono", "che ora è", "dimmi l'ora", "ora è", "ore sono"],
    "data":          ["che giorno", "che data", "data di oggi", "giorno è", "giorno siamo"],
    "meteo":         ["meteo", "tempo che fa", "che tempo fa", "previsioni"],
    "batteria":      ["batteria", "carica del pc", "quanta carica"],
    "ram":           ["ram", "memoria ram", "uso memoria"],
    "cpu":           ["cpu", "processore", "uso processore", "utilizzo cpu"],
    "disco":         ["disco", "spazio disco", "spazio libero", "hard disk"],
    "chrome":        ["chrome", "google chrome", "apri chrome", "apri google chrome",
                      "lancia chrome", "avvia chrome", "vai su chrome"],
    "google":        ["cerca su google", "fai una ricerca", "cerca su internet", "cerca in rete",
                      "ricerca su google", "ricerca su chrome", "cerca su chrome",
                      "fai una ricerca su chrome", "fai una ricerca su google",
                      "cerca online", "vai su google", "apri google"],
    "youtube":       ["youtube", "apri youtube", "vai su youtube", "lancia youtube",
                      "cerca su youtube", "ricerca su youtube"],
    "netflix":       ["netflix", "apri netflix", "vai su netflix", "lancia netflix"],
    "spotify":       ["spotify", "apri spotify", "vai su spotify", "lancia spotify"],
    "whatsapp":      ["whatsapp", "apri whatsapp", "vai su whatsapp"],
    "gmail":         ["gmail", "apri gmail", "apri email", "posta elettronica", "vai su gmail"],
    "instagram":     ["instagram", "apri instagram", "vai su instagram"],
    "twitter":       ["twitter", "apri twitter", "vai su twitter", "apri x"],
    "tiktok":        ["tiktok", "apri tiktok", "vai su tiktok"],
    "maps":          ["maps", "google maps", "apri maps", "come arrivo", "indicazioni per", "naviga verso"],
    "amazon":        ["amazon", "apri amazon", "vai su amazon"],
    "notepad":       ["blocco note", "notepad", "apri blocco note", "apri notepad", "testo"],
    "calc":          ["calcolatrice", "apri calcolatrice", "apri la calcolatrice"],
    "explorer":      ["esplora file", "file explorer", "cartelle", "apri esplora", "gestione file"],
    "taskman":       ["task manager", "gestione attivita", "processi", "apri task manager"],
    "settings":      ["impostazioni", "settings", "pannello di controllo", "apri impostazioni"],
    "screenshot":    ["screenshot", "schermata", "cattura schermo", "foto schermo", "cattura"],
    "paint":         ["paint", "apri paint", "disegna"],
    "word":          ["word", "apri word", "microsoft word", "documento word"],
    "excel":         ["excel", "apri excel", "foglio di calcolo", "foglio excel"],
    "powerpoint":    ["powerpoint", "apri powerpoint", "presentazione"],
    "vscode":        ["visual studio code", "vscode", "apri vscode", "apri visual studio"],
    "discord":       ["discord", "apri discord", "vai su discord", "lancia discord"],
    "spegni_pc":     ["spegni il pc", "spegni il computer", "spegni sistema", "spegni pc"],
    "riavvia_pc":    ["riavvia il pc", "riavvia il computer", "riavvia sistema", "riavvia pc"],
    "blocca_pc":     ["blocca pc", "blocca schermo", "blocca computer", "blocca il pc"],
    "ciao":          ["ciao", "salve", "hey", "buongiorno", "buonasera", "buon pomeriggio"],
    "come_stai":     ["come stai", "come va", "tutto bene", "stai bene"],
    "grazie":        ["grazie", "ti ringrazio", "perfetto grazie"],
    "chi_sei":       ["chi sei", "cosa sei", "presentati", "chi è jarvis"],
    "calcolo":       ["quanto fa", "calcola", "quant'è", "risultato di"],
    "timer":         ["timer", "conto alla rovescia", "imposta timer"],
    "traduzione":    ["traduci", "traduzione", "come si dice"],
    "notizie":       ["notizie", "ultime notizie", "cosa e' successo", "news"],
    "apri_cartella": ["apri la cartella", "apri cartella", "apri documenti", "apri download", "apri desktop"],
    "apri_file":     ["apri il file", "apri file"],
    "luminosita":    ["luminosita", "luminosità", "alza luminosita", "abbassa luminosita"],
    "email_invia":   ["invia email", "manda email", "scrivi email"],
    "email_leggi":   ["leggi email", "leggi le email", "nuove email", "controlla email"],
    "hue":           ["accendi la luce", "spegni la luce", "philips hue", "luci"],
    "chatgpt":       ["chiedi a gpt", "gpt", "intelligenza artificiale", "chiedi all'ia"],
}

def _match(command, key):
    return any(k in command for k in _SYNONYMS.get(key, []))

# ── Execute ────────────────────────────────────────────────────────────────────
def execute(command):
    _log(command)
    c = command.strip().lower()

    # Stop
    if _match(c, "stop"):
        speak("Vado in standby. A presto!")
        if _shutdown_callback:
            _shutdown_callback()
        return

    # Calcolo matematico (offline)
    if _match(c, "calcolo"):
        _do_math(c)
        return

    # Musica
    if _match(c, "musica_play"):
        song = _extract_query(c, _SYNONYMS["musica_play"])
        if song:
            if "spotify" in c:
                if _require_network():
                    webbrowser.open(f"https://open.spotify.com/search/{song}")
                    speak(f"Cerco {song} su Spotify")
            else:
                if _require_network():
                    _open_chrome(f"https://www.youtube.com/results?search_query={song}")
                    speak(f"Metto {song} su YouTube")
        else:
            if _require_network():
                webbrowser.open("https://open.spotify.com")
                speak("Apro Spotify")
        return

    # Media controls
    if _match(c, "media_pause"):
        pyautogui.press("playpause"); speak("Messo in pausa"); return
    if _match(c, "media_resume"):
        pyautogui.press("playpause"); speak("Riprendo"); return
    if _match(c, "media_next"):
        pyautogui.press("nexttrack"); speak("Canzone successiva"); return
    if _match(c, "media_prev"):
        pyautogui.press("prevtrack"); speak("Canzone precedente"); return

    # Volume
    if _match(c, "vol_up"):
        v = _get_volume()
        nv = min(100, v + 20) if v >= 0 else -1
        if nv >= 0: _set_volume(nv); speak(f"Volume al {nv} percento")
        else: pyautogui.press("volumeup", presses=5); speak("Volume alzato")
        return
    if _match(c, "vol_down"):
        v = _get_volume()
        nv = max(0, v - 20) if v >= 0 else -1
        if nv >= 0: _set_volume(nv); speak(f"Volume al {nv} percento")
        else: pyautogui.press("volumedown", presses=5); speak("Volume abbassato")
        return
    if _match(c, "vol_mute"):
        pyautogui.press("volumemute"); speak("Audio silenziato"); return
    if _match(c, "vol_query"):
        v = _get_volume()
        speak(f"Il volume e' al {v} percento" if v >= 0 else "Non riesco a leggere il volume")
        return
    if "volume" in c:
        m = re.search(r"\b(\d{1,3})\b", c)
        if m:
            _set_volume(int(m.group(1)))
            speak(f"Volume impostato al {m.group(1)} percento")
        else:
            speak("Non ho capito il livello del volume")
        return

    # Sveglia
    if _match(c, "sveglia"):
        q = _extract_query(c, _SYNONYMS["sveglia"])
        _set_alarm(q) if q else speak("A che ora vuoi la sveglia?")
        return

    # Promemoria
    if _match(c, "promemoria"):
        q = _extract_query(c, ["ricordami di", "ricordami", "promemoria"])
        if q:
            speak(f"Ok, ti ricorderò di {q}")
            _reminders.append(q)
        return

    # Ora / Data (offline)
    if _match(c, "ora"):
        speak(f"Sono le {datetime.datetime.now().strftime('%H:%M')}"); return
    if _match(c, "data"):
        giorni = ["lunedi","martedi","mercoledi","giovedi","venerdi","sabato","domenica"]
        oggi = datetime.datetime.now()
        speak(f"Oggi e' {giorni[oggi.weekday()]} {oggi.strftime('%d %B %Y')}"); return

    # Meteo
    if _match(c, "meteo"):
        if _require_network():
            city = _extract_query(c, ["meteo a","meteo di","meteo","tempo a"])
            q = f"meteo {city}" if city else "meteo oggi"
            webbrowser.open(f"https://www.google.com/search?q={q}")
            speak(f"Apro il meteo{' per '+city if city else ''}")
        return

    # Sistema (offline)
    if _match(c, "batteria"):
        b = psutil.sensors_battery()
        if b:
            speak(f"Batteria al {int(b.percent)} percento, {'in carica' if b.power_plugged else 'non in carica'}")
        else:
            speak("Non riesco a leggere la batteria")
        return
    if _match(c, "ram"):
        m = psutil.virtual_memory()
        speak(f"RAM: {int(m.percent)} percento su {round(m.total/1e9,1)} gigabyte"); return
    if _match(c, "cpu"):
        speak(f"CPU al {psutil.cpu_percent(interval=1)} percento"); return
    if _match(c, "disco"):
        d = psutil.disk_usage("/")
        speak(f"Disco: {round(d.free/1e9,1)} GB liberi su {round(d.total/1e9,1)} GB"); return

    # App browser (richiedono rete)
    if _match(c, "chrome"):
        q = _extract_query(c, ["apri chrome e cerca","cerca su chrome","cerca","ricerca"])
        if _require_network():
            _open_chrome(f"https://www.google.com/search?q={q}" if q else None)
            speak(f"Cerco {q} su Chrome" if q else "Apro Chrome")
        return
    if _match(c, "google"):
        q = _extract_query(c, ["cerca su google","cerca su internet","fai una ricerca su","cerca"])
        if q:
            if _require_network(): _open_chrome(f"https://www.google.com/search?q={q}"); speak(f"Cerco {q}")
        else:
            speak("Cosa vuoi cercare?")
        return
    if _match(c, "youtube"):
        if _require_network():
            q = _extract_query(c, ["cerca su youtube","apri youtube e cerca","youtube"])
            url = f"https://www.youtube.com/results?search_query={q}" if q else "https://www.youtube.com"
            _open_chrome(url); speak(f"Cerco {q} su YouTube" if q else "Apro YouTube")
        return
    if _match(c, "netflix"):
        if _require_network(): webbrowser.open("https://www.netflix.com"); speak("Apro Netflix")
        return
    if _match(c, "spotify"):
        if _require_network(): webbrowser.open("https://open.spotify.com"); speak("Apro Spotify")
        return
    if _match(c, "whatsapp"):
        if _require_network(): webbrowser.open("https://web.whatsapp.com"); speak("Apro WhatsApp")
        return
    if _match(c, "gmail"):
        if _require_network(): webbrowser.open("https://mail.google.com"); speak("Apro Gmail")
        return
    if _match(c, "instagram"):
        if _require_network(): webbrowser.open("https://www.instagram.com"); speak("Apro Instagram")
        return
    if _match(c, "twitter"):
        if _require_network(): webbrowser.open("https://www.twitter.com"); speak("Apro Twitter")
        return
    if _match(c, "tiktok"):
        if _require_network(): webbrowser.open("https://www.tiktok.com"); speak("Apro TikTok")
        return
    if _match(c, "amazon"):
        if _require_network(): webbrowser.open("https://www.amazon.it"); speak("Apro Amazon")
        return
    if _match(c, "maps"):
        if _require_network():
            q = _extract_query(c, ["indicazioni per", "come arrivo a", "naviga verso", "maps"])
            if q:
                webbrowser.open(f"https://www.google.com/maps/search/{q}")
                speak(f"Apro Maps per {q}")
            else:
                webbrowser.open("https://www.google.com/maps")
                speak("Apro Google Maps")
        return

    # App locali (offline)
    if _match(c, "notepad"):
        subprocess.Popen("notepad.exe"); speak("Apro il blocco note"); return
    if _match(c, "calc"):
        subprocess.Popen("calc.exe"); speak("Apro la calcolatrice"); return
    if _match(c, "explorer"):
        subprocess.Popen("explorer.exe"); speak("Apro esplora file"); return
    if _match(c, "taskman"):
        subprocess.Popen("taskmgr.exe"); speak("Apro il task manager"); return
    if _match(c, "settings"):
        subprocess.Popen("ms-settings:", shell=True); speak("Apro le impostazioni"); return
    if _match(c, "screenshot"):
        subprocess.Popen("snippingtool"); speak("Apro lo strumento di cattura"); return
    if _match(c, "paint"):
        subprocess.Popen("mspaint.exe"); speak("Apro Paint"); return
    if _match(c, "word"):
        subprocess.Popen("winword.exe", shell=True); speak("Apro Word"); return
    if _match(c, "excel"):
        subprocess.Popen("excel.exe", shell=True); speak("Apro Excel"); return
    if _match(c, "powerpoint"):
        subprocess.Popen("powerpnt.exe", shell=True); speak("Apro PowerPoint"); return
    if _match(c, "vscode"):
        subprocess.Popen("code", shell=True); speak("Apro Visual Studio Code"); return
    if _match(c, "discord"):
        # Prova ad aprire l'app installata, altrimenti apre il browser
        discord_paths = [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Discord", "Update.exe"),
            os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu",
                         "Programs", "Discord Inc", "Discord.lnk"),
        ]
        if "chrome" in c or "browser" in c or "web" in c:
            if _require_network(): webbrowser.open("https://discord.com/app"); speak("Apro Discord nel browser")
        else:
            opened = False
            for path in discord_paths:
                if os.path.exists(path):
                    subprocess.Popen([path, "--processStart", "Discord.exe"])
                    speak("Apro Discord")
                    opened = True
                    break
            if not opened:
                if _require_network(): webbrowser.open("https://discord.com/app"); speak("Apro Discord nel browser")
        return

    # PC
    if _match(c, "spegni_pc"):
        speak("Spengo il computer tra 10 secondi"); os.system("shutdown /s /t 10"); return
    if _match(c, "riavvia_pc"):
        speak("Riavvio il computer tra 10 secondi"); os.system("shutdown /r /t 10"); return
    if _match(c, "blocca_pc"):
        os.system("rundll32.exe user32.dll,LockWorkStation"); speak("Schermo bloccato"); return

    # Chiacchiera (offline)
    if _match(c, "ciao"):
        ora = datetime.datetime.now().hour
        if ora < 12:   speak("Buongiorno! Come posso aiutarti?")
        elif ora < 18: speak("Buon pomeriggio! Dimmi pure.")
        else:          speak("Buonasera! In cosa posso esserti utile?")
        return
    if _match(c, "come_stai"):
        speak("Sto benissimo, grazie! Pronto ad aiutarti."); return
    if _match(c, "grazie"):
        speak("Prego! Sono qui se hai bisogno."); return
    if _match(c, "chi_sei"):
        speak("Sono Jarvis, il tuo assistente vocale. Sono qui per aiutarti."); return

    # Wikipedia / Google
    if any(k in c for k in ["chi è","chi e'","cos'è","cosa è","quanto","quando",
                              "dove","come funziona","dimmi","spiegami","parlami di"]):
        if _require_network():
            if _has_gpt_key(): _ask_gpt(c)
            else: _answer_question(c)
        return

    # Timer
    if _match(c, "timer"):
        q = _extract_query(c, _SYNONYMS["timer"])
        _set_timer(q) if q else speak("Per quanti minuti vuoi il timer?")
        return

    # Traduzione
    if _match(c, "traduzione"):
        if _require_network(): _translate(c)
        return

    # Notizie
    if _match(c, "notizie"):
        if _require_network(): _read_news()
        return

    # Apri cartella
    if _match(c, "apri_cartella"):
        _open_folder(c)
        return

    # Apri file
    if _match(c, "apri_file"):
        q = _extract_query(c, _SYNONYMS["apri_file"])
        if q: _open_file(q)
        else: speak("Quale file vuoi aprire?")
        return

    # Luminosità
    if _match(c, "luminosita"):
        _set_brightness(c)
        return

    # Email
    if _match(c, "email_invia"):
        if _require_network(): _send_email(c)
        return
    if _match(c, "email_leggi"):
        if _require_network(): _read_emails()
        return

    # Philips Hue
    if _match(c, "hue"):
        if _require_network(): _control_hue(c)
        return

    # ChatGPT esplicito
    if _match(c, "chatgpt"):
        if _require_network(): _ask_gpt(c)
        return

    # ── FALLBACK UNIVERSALE: qualsiasi cosa non riconosciuta va a GPT/Wikipedia ──
    if _is_online():
        _ask_gpt(c)
    else:
        speak("Sono offline. Posso aiutarti solo con comandi locali come orario, data, calcolatrice e app.")


# ── Calcolo matematico ────────────────────────────────────────────────────────
def _do_math(command):
    expr = command
    for w in ["quanto fa","calcola","quant'è","risultato di"]:
        expr = expr.replace(w, "")
    expr = expr.strip()
    # sostituisce parole con simboli
    expr = expr.replace("per","*").replace("diviso","/").replace("più","+").replace("meno","-")
    expr = re.sub(r"[^0-9\+\-\*\/\.\(\) ]", "", expr).strip()
    try:
        result = eval(expr)
        speak(f"Il risultato è {result}")
    except Exception:
        speak("Non sono riuscito a calcolare il risultato")


# ── Sveglia ────────────────────────────────────────────────────────────────────
def _set_alarm(time_str):
    match = re.search(r"(\d{1,2})[:\.]?(\d{0,2})", time_str)
    if not match:
        speak("Non ho capito l'orario della sveglia"); return
    hour   = int(match.group(1))
    minute = int(match.group(2)) if match.group(2) else 0
    speak(f"Sveglia impostata per le {hour}:{minute:02d}")

    def _run():
        while True:
            now = datetime.datetime.now()
            if now.hour == hour and now.minute == minute:
                speak(f"Sveglia! Sono le {hour}:{minute:02d}"); break
            time.sleep(20)
    threading.Thread(target=_run, daemon=True).start()


# ── Wikipedia ─────────────────────────────────────────────────────────────────
def _answer_question(command):
    speak("Un momento, cerco la risposta.")
    query = command
    for w in ["chi e'","chi è","cos'è","cosa è","dimmi","spiegami","cosa sai di",
              "parlami di","quanto è","quanto e'","come funziona","dove si trova","quando"]:
        query = query.replace(w, "").strip()

    try:
        page = wiki.page(query)
        if page.exists():
            sentences = page.summary.split(". ")
            speak(". ".join(sentences[:2]) + ".")
            return
    except Exception:
        pass

    answer = _google_snippet(query)
    if answer:
        speak(answer)
    else:
        speak(f"Non ho trovato una risposta per: {query}")


def _google_snippet(query):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(f"https://www.google.com/search?q={query}&hl=it",
                           headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        for tag in soup.select(".hgKElc,.IZ6rdc,.yDYNvb,.LGOjhe,.kno-rdesc span"):
            text = tag.get_text()
            if len(text) > 20:
                return text[:300]
    except Exception:
        pass
    return ""


def _open_chrome(url=None):
    target = url or "https://www.google.com"
    chrome_running = any("chrome" in p.name().lower()
                         for p in psutil.process_iter(["name"]))
    for path in [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                 r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]:
        if os.path.exists(path):
            flag = "--new-tab" if chrome_running else ""
            args = [path, flag, target] if flag else [path, target]
            subprocess.Popen(args)
            return
    webbrowser.open(target)


def _extract_query(command, keywords):
    for kw in sorted(keywords, key=len, reverse=True):
        if kw in command:
            q = command.split(kw, 1)[-1].strip()
            if q: return q
    return ""


# ── Timer ───────────────────────────────────────────────────────────────────────────
def _set_timer(text):
    m = re.search(r"(\d+)\s*(minuti?|secondi?|ore?)", text)
    if not m:
        speak("Non ho capito la durata del timer")
        return
    amount = int(m.group(1))
    unit   = m.group(2)
    if "sec" in unit:   seconds = amount
    elif "or" in unit:  seconds = amount * 3600
    else:               seconds = amount * 60
    speak(f"Timer impostato per {amount} {unit}")

    def _run():
        time.sleep(seconds)
        speak(f"Timer scaduto! Sono passati {amount} {unit}")
    threading.Thread(target=_run, daemon=True).start()


# ── Traduzione ───────────────────────────────────────────────────────────────────────
def _translate(command):
    from deep_translator import GoogleTranslator
    _LANGS = {
        "inglese": "en", "francese": "fr", "spagnolo": "es",
        "tedesco": "de", "portoghese": "pt", "cinese": "zh-CN",
        "giapponese": "ja", "russo": "ru", "arabo": "ar",
    }
    target_lang = "en"
    for name, code in _LANGS.items():
        if name in command:
            target_lang = code
            break
    # Rimuove parole chiave per estrarre il testo
    text = command
    for kw in ["traduci", "traduzione", "come si dice", "in " + next(
            (n for n in _LANGS if n in command), "")]:
        text = text.replace(kw, "").strip()
    if not text:
        speak("Cosa vuoi tradurre?")
        return
    try:
        result = GoogleTranslator(source="auto", target=target_lang).translate(text)
        speak(f"La traduzione e': {result}")
    except Exception:
        speak("Non sono riuscito a tradurre")


# ── Notizie ───────────────────────────────────────────────────────────────────────────
def _read_news():
    try:
        url = "https://news.google.com/rss?hl=it&gl=IT&ceid=IT:it"
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.content, "xml")
        items = soup.find_all("item")[:5]
        if not items:
            speak("Non ho trovato notizie")
            return
        speak("Ecco le ultime notizie:")
        for i, item in enumerate(items, 1):
            title = item.find("title").get_text()
            speak(f"{i}. {title}")
    except Exception:
        speak("Non riesco a leggere le notizie al momento")


# ── Apri cartella / file ───────────────────────────────────────────────────────────
def _open_folder(command):
    _FOLDERS = {
        "documenti":  os.path.expanduser("~/Documents"),
        "download":   os.path.expanduser("~/Downloads"),
        "desktop":    os.path.expanduser("~/Desktop"),
        "immagini":   os.path.expanduser("~/Pictures"),
        "musica":     os.path.expanduser("~/Music"),
        "video":      os.path.expanduser("~/Videos"),
    }
    for name, path in _FOLDERS.items():
        if name in command:
            subprocess.Popen(["explorer.exe", path])
            speak(f"Apro la cartella {name}")
            return
    # Cartella generica
    q = _extract_query(command, ["apri la cartella", "apri cartella", "vai nella cartella"])
    if q:
        path = os.path.expanduser(f"~/{q}")
        if os.path.exists(path):
            subprocess.Popen(["explorer.exe", path])
            speak(f"Apro {q}")
        else:
            speak(f"Non trovo la cartella {q}")
    else:
        subprocess.Popen("explorer.exe")
        speak("Apro esplora file")


def _open_file(name):
    search_dirs = [
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Downloads"),
    ]
    for d in search_dirs:
        for f in os.listdir(d):
            if name.lower() in f.lower():
                os.startfile(os.path.join(d, f))
                speak(f"Apro {f}")
                return
    speak(f"Non ho trovato il file {name}")


# ── Luminosità ─────────────────────────────────────────────────────────────────────────
def _set_brightness(command):
    try:
        import screen_brightness_control as sbc
        current = sbc.get_brightness()[0]
        m = re.search(r"\b(\d{1,3})\b", command)
        if m:
            sbc.set_brightness(int(m.group(1)))
            speak(f"Luminosità impostata al {m.group(1)} percento")
        elif any(k in command for k in ["alza", "aumenta", "più"]):
            nv = min(100, current + 20)
            sbc.set_brightness(nv)
            speak(f"Luminosità alzata al {nv} percento")
        elif any(k in command for k in ["abbassa", "diminuisci", "meno"]):
            nv = max(0, current - 20)
            sbc.set_brightness(nv)
            speak(f"Luminosità abbassata al {nv} percento")
        else:
            speak(f"Luminosità attuale: {current} percento")
    except Exception:
        speak("Non riesco a controllare la luminosità su questo schermo")


# ── Email ─────────────────────────────────────────────────────────────────────────────
def _send_email(command):
    import smtplib
    from email.mime.text import MIMEText
    from config import EMAIL_ADDRESS, EMAIL_PASSWORD, EMAIL_SMTP, EMAIL_PORT
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        speak("Configura le credenziali email in config.py per usare questa funzione")
        return
    # Estrai destinatario e testo
    to_match = re.search(r"a\s+([\w.]+@[\w.]+)", command)
    if not to_match:
        speak("Non ho trovato un indirizzo email nel comando")
        return
    to_addr = to_match.group(1)
    body = _extract_query(command, ["con testo", "con messaggio", "dicendo"]) or "Messaggio inviato da Jarvis"
    try:
        msg = MIMEText(body)
        msg["Subject"] = "Messaggio da Jarvis"
        msg["From"]    = EMAIL_ADDRESS
        msg["To"]      = to_addr
        with smtplib.SMTP(EMAIL_SMTP, EMAIL_PORT) as s:
            s.starttls()
            s.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            s.send_message(msg)
        speak(f"Email inviata a {to_addr}")
    except Exception as e:
        speak("Non sono riuscito a inviare l'email")


def _read_emails():
    import imaplib
    import email as emaillib
    from config import EMAIL_ADDRESS, EMAIL_PASSWORD, EMAIL_IMAP
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        speak("Configura le credenziali email in config.py per usare questa funzione")
        return
    try:
        mail = imaplib.IMAP4_SSL(EMAIL_IMAP)
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        mail.select("inbox")
        _, data = mail.search(None, "UNSEEN")
        ids = data[0].split()
        if not ids:
            speak("Non hai nuove email")
            return
        speak(f"Hai {len(ids)} email non lette. Leggo le ultime tre.")
        for uid in ids[-3:]:
            _, msg_data = mail.fetch(uid, "(RFC822)")
            msg = emaillib.message_from_bytes(msg_data[0][1])
            sender  = msg["From"] or "sconosciuto"
            subject = msg["Subject"] or "nessun oggetto"
            speak(f"Da {sender}: {subject}")
        mail.logout()
    except Exception:
        speak("Non riesco a leggere le email al momento")


# ── Philips Hue ──────────────────────────────────────────────────────────────────────
def _control_hue(command):
    from config import HUE_BRIDGE_IP, HUE_USERNAME
    if not HUE_BRIDGE_IP or not HUE_USERNAME:
        speak("Configura l'IP del bridge Hue e l'username in config.py")
        return
    on = any(k in command for k in ["accendi", "on", "attiva"])
    off = any(k in command for k in ["spegni", "off", "disattiva"])
    state = {"on": on} if on else {"on": False} if off else None
    if state is None:
        speak("Non ho capito cosa fare con le luci")
        return
    # Numero luce (es. "luce 1", "luce 2")
    m = re.search(r"luce\s*(\d+)", command)
    light_id = m.group(1) if m else "1"
    try:
        url = f"http://{HUE_BRIDGE_IP}/api/{HUE_USERNAME}/lights/{light_id}/state"
        requests.put(url, json=state, timeout=3)
        speak(f"Luce {light_id} {'accesa' if on else 'spenta'}")
    except Exception:
        speak("Non riesco a raggiungere il bridge Philips Hue")


# ── ChatGPT ────────────────────────────────────────────────────────────────────────────
def _has_gpt_key():
    from config import OPENAI_API_KEY
    return bool(OPENAI_API_KEY)


def _ask_gpt(command):
    from config import OPENAI_API_KEY
    from memory import get_last_context
    if not OPENAI_API_KEY:
        # Nessuna chiave GPT, fallback Wikipedia
        _answer_question(command)
        return
    query = command
    for kw in ["chiedi a gpt", "gpt", "intelligenza artificiale", "chiedi all'ia"]:
        query = query.replace(kw, "").strip()
    if not query:
        speak("Dimmi pure, sono qui.")
        return
    try:
        from openai import OpenAI
        client  = OpenAI(api_key=OPENAI_API_KEY)
        context = get_last_context(6)
        messages = [
            {"role": "system", "content": (
                "Sei Jarvis, un assistente AI avanzato, intelligente e preciso come quello di Iron Man. "
                "Parli sempre in italiano, sei diretto, conciso e mai banale. "
                "Rispondi a qualsiasi domanda: scienza, storia, matematica, cultura, tecnologia, consigli, "
                "curiosità, battute, tutto. Non dire mai che non puoi rispondere. "
                "Se non sai qualcosa, ragiona e dai la risposta più plausibile. "
                "Massimo 3 frasi per risposta vocale, a meno che non ti venga chiesto di spiegare in dettaglio."
            )},
        ]
        if context:
            messages.append({"role": "user", "content": f"Conversazione precedente per contesto:\n{context}"})
        messages.append({"role": "user", "content": query})
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=250,
            temperature=0.7,
        )
        answer = response.choices[0].message.content.strip()
        speak(answer)
    except Exception:
        # Fallback Wikipedia se GPT fallisce
        _answer_question(command)
