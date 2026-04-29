import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty("voices")

print("Voci disponibili:\n")
for i, voice in enumerate(voices):
    print(f"[{i}] Nome: {voice.name}")
    print(f"     ID: {voice.id}")
    print()

# Prova a parlare con la prima voce disponibile
engine.say("Ciao, sono Jarvis, il tuo assistente vocale")
engine.runAndWait()
