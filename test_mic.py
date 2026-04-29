import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
BLOCK_SIZE = 1024

print("Parla nel microfono per 10 secondi, guarda i valori di ampiezza...")
print("(premi CTRL+C per fermare)\n")

with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=BLOCK_SIZE) as stream:
    for _ in range(int(10 * SAMPLE_RATE / BLOCK_SIZE)):
        block, _ = stream.read(BLOCK_SIZE)
        amplitude = np.abs(block).mean()
        bar = "#" * int(amplitude / 50)
        print(f"Ampiezza: {amplitude:.1f}  {bar}")
