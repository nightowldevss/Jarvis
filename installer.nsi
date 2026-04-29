; ╔══════════════════════════════════════════════════════╗
; ║         J.A.R.V.I.S  —  NSIS Installer Script       ║
; ╚══════════════════════════════════════════════════════╝

!include "MUI2.nsh"
!include "LogicLib.nsh"

; ── Info applicazione ──────────────────────────────────
Name              "J.A.R.V.I.S"
OutFile           "Jarvis-Setup.exe"
InstallDir        "$LOCALAPPDATA\Jarvis"
InstallDirRegKey  HKCU "Software\Jarvis" "InstallDir"
RequestExecutionLevel user
Unicode True

; ── Icona e grafica ────────────────────────────────────
!define MUI_ICON              "jarvis.ico"
!define MUI_UNICON             "jarvis.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP_NOSTRETCH
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_RIGHT
!define MUI_BGCOLOR            "070810"
!define MUI_TEXTCOLOR          "00D4FF"

; ── Pagine installer ───────────────────────────────────
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; ── Pagine uninstaller ─────────────────────────────────
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; ── Lingua ─────────────────────────────────────────────
!insertmacro MUI_LANGUAGE "Italian"

; ── Versione ───────────────────────────────────────────
VIProductVersion "1.0.0.0"
VIAddVersionKey /LANG=0 "ProductName"     "J.A.R.V.I.S"
VIAddVersionKey /LANG=0 "ProductVersion"  "1.0.0"
VIAddVersionKey /LANG=0 "CompanyName"     "Jarvis Project"
VIAddVersionKey /LANG=0 "FileDescription" "J.A.R.V.I.S Assistente Vocale"
VIAddVersionKey /LANG=0 "FileVersion"     "1.0.0"

; ══════════════════════════════════════════════════════
; SEZIONE INSTALLAZIONE
; ══════════════════════════════════════════════════════
Section "Jarvis" SecMain

    SetOutPath "$INSTDIR"

    ; ── Copia tutti i file ─────────────────────────────
    File "jarvis.ico"
    File "version.json"
    File "requirements.txt"

    ; File Python compilati (.pyc) — codice protetto
    File /nonfatal "gui.pyc"
    File /nonfatal "commands.pyc"
    File /nonfatal "listener.pyc"
    File /nonfatal "speaker.pyc"
    File /nonfatal "memory.pyc"
    File /nonfatal "updater.pyc"
    File /nonfatal "main.pyc"

    ; File di configurazione (visibile all'utente)
    File "config.py"

    ; Modello Vosk
    SetOutPath "$INSTDIR\vosk-model-it"
    File /r "vosk-model-it\*.*"

    ; Cartella dati
    CreateDirectory "$INSTDIR\data"

    SetOutPath "$INSTDIR"

    ; ── Installa dipendenze Python ─────────────────────
    DetailPrint "Installazione dipendenze Python..."
    nsExec::ExecToLog 'python -m pip install --quiet speechrecognition pyttsx3 sounddevice numpy vosk wikipedia-api requests beautifulsoup4 psutil pyautogui pycaw keyboard pystray pillow deep-translator openai screen-brightness-control winshell pywin32 packaging'

    ; ── Crea Jarvis.bat launcher ──────────────────────
    FileOpen $0 "$INSTDIR\Jarvis.bat" w
    FileWrite $0 '@echo off$\r$\n'
    FileWrite $0 'start "" pythonw "$INSTDIR\gui.pyc"$\r$\n'
    FileClose $0

    ; ── Collegamento Desktop con icona ─────────────────
    CreateShortcut "$DESKTOP\Jarvis.lnk" \
        "$INSTDIR\Jarvis.bat" "" \
        "$INSTDIR\jarvis.ico" 0 \
        SW_SHOWMINIMIZED "" "J.A.R.V.I.S - Assistente Vocale"

    ; ── Collegamento Menu Start ────────────────────────
    CreateDirectory "$SMPROGRAMS\Jarvis"
    CreateShortcut "$SMPROGRAMS\Jarvis\Jarvis.lnk" \
        "$INSTDIR\Jarvis.bat" "" \
        "$INSTDIR\jarvis.ico" 0 \
        SW_SHOWMINIMIZED "" "J.A.R.V.I.S - Assistente Vocale"
    CreateShortcut "$SMPROGRAMS\Jarvis\Disinstalla Jarvis.lnk" \
        "$INSTDIR\Uninstall.exe"

    ; ── Registro di sistema ────────────────────────────
    WriteRegStr HKCU "Software\Jarvis" "InstallDir" "$INSTDIR"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Jarvis" \
        "DisplayName" "J.A.R.V.I.S Assistente Vocale"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Jarvis" \
        "DisplayVersion" "1.0.0"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Jarvis" \
        "Publisher" "Jarvis Project"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Jarvis" \
        "InstallLocation" "$INSTDIR"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Jarvis" \
        "DisplayIcon" "$INSTDIR\jarvis.ico"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Jarvis" \
        "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Jarvis" \
        "NoModify" 1
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Jarvis" \
        "NoRepair" 1

    ; ── Crea uninstaller ───────────────────────────────
    WriteUninstaller "$INSTDIR\Uninstall.exe"

SectionEnd

; ══════════════════════════════════════════════════════
; SEZIONE DISINSTALLAZIONE
; ══════════════════════════════════════════════════════
Section "Uninstall"

    ; Rimuovi file
    RMDir /r "$INSTDIR"

    ; Rimuovi collegamenti
    Delete "$DESKTOP\Jarvis.lnk"
    RMDir /r "$SMPROGRAMS\Jarvis"

    ; Rimuovi registro
    DeleteRegKey HKCU "Software\Jarvis"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Jarvis"

SectionEnd
