from listener import listen
from speaker import speak
from commands import execute
from config import WAKE_WORD

def main():
    speak("Jarvis attivo. Dimmi pure!")
    print(f"In ascolto... (dì '{WAKE_WORD}' per attivare)\n")

    while True:
        # Ascolta per 4 secondi cercando la wake word
        text = listen(timeout=4)

        if WAKE_WORD in text:
            command = text.replace(WAKE_WORD, "").strip().strip(",").strip()

            if command:
                execute(command)
            else:
                speak("Dimmi pure!")
                command = listen(prompt="In ascolto del comando...", timeout=6)
                if command:
                    execute(command)
                else:
                    speak("Non ho sentito nulla.")

if __name__ == "__main__":
    main()
