
import sounddevice as sd
import soundfile as sf
from pathlib import Path

# ==========================================
# MICROPHONE CONFIGURATION
# ==========================================

SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 1024

OUTPUT_FILE = (
    Path(__file__).resolve().parent
    / "live_command.wav"
)

# ==========================================
# MICROPHONE RECORDING
# ==========================================

audio_chunks = []


def audio_callback(indata, frames, time_info, status):
    if status:
        print("Audio warning:", status)

    audio_chunks.append(indata.copy())


print("\nMicrophone ready!")
input("Press Enter to START recording...")

print("\nRecording... Speak your command.")
print("Press Enter again to STOP recording.\n")

with sd.InputStream(
    samplerate=SAMPLE_RATE,
    channels=CHANNELS,
    dtype="float32",
    blocksize=BLOCK_SIZE,
    callback=audio_callback
):
    input()

# ==========================================
# SAVE AUDIO
# ==========================================

import numpy as np

if not audio_chunks:
    print("No audio was recorded.")
    raise SystemExit(1)

audio = np.concatenate(audio_chunks, axis=0)

sf.write(
    str(OUTPUT_FILE),
    audio,
    SAMPLE_RATE
)

duration = len(audio) / SAMPLE_RATE

print("\nRecording completed!")
print(f"Recording duration: {duration:.2f} seconds")
print(f"Audio saved to: {OUTPUT_FILE}")
