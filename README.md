# J.A.R.V.I.S — Assistente Vocale

Assistente vocale intelligente per Windows, ispirato a Jarvis di Iron Man.

## Installazione

### 1. Scarica il setup
Vai su [Releases](https://github.com/nightowldevss/Jarvis/releases/latest) e scarica `Jarvis-Setup.exe`

### 2. Sblocca il file (necessario al primo avvio)
Windows potrebbe bloccare il file perché non è firmato digitalmente.

**Metodo A — Tasto destro:**
1. Tasto destro su `Jarvis-Setup.exe`
2. Clicca **Proprietà**
3. In fondo spunta **Sblocca**
4. Clicca **OK**
5. Avvia il setup normalmente

**Metodo B — Se compare "App non riconosciuta":**
1. Clicca **Ulteriori informazioni**
2. Clicca **Esegui comunque**

### 3. Segui il setup
Il setup installerà automaticamente tutto il necessario.

---

## Comandi vocali

| Comando | Azione |
|---|---|
| "Jarvis, che ore sono" | Dice l'orario |
| "Jarvis, apri Chrome" | Apre Google Chrome |
| "Jarvis, metti [canzone]" | Cerca su YouTube |
| "Jarvis, traduci [testo] in inglese" | Traduce |
| "Jarvis, ultime notizie" | Legge le notizie |
| "Jarvis, imposta timer 5 minuti" | Timer |
| "Jarvis, quanto fa 15 per 8" | Calcolo |
| "Jarvis, apri documenti" | Apre cartella |
| "Jarvis, disattivati" | Va in standby |

Hotkey predefinita: **Ctrl+Shift+J**

---

## Configurazione API OpenAI (opzionale)
Per risposte più intelligenti, inserisci la tua chiave API in `config.py`:
```
OPENAI_API_KEY = "sk-..."
```
Ottieni una chiave su [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

---

## Requisiti
- Windows 10/11
- Python 3.9+
- Microfono
- Connessione internet (per riconoscimento vocale e risposte)
