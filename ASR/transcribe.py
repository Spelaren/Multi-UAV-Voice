import os
from pathlib import Path

nvidia_dir = (
    Path(__file__).resolve().parent.parent
    / ".venv"
    / "Lib"
    / "site-packages"
    / "nvidia"
)

dll_directories = []

for folder in ["cublas", "cudnn", "cuda_nvrtc"]:
    dll_path = nvidia_dir / folder / "bin"

    if dll_path.exists():
        dll_directories.append(os.add_dll_directory(str(dll_path)))
        print(f"Added CUDA DLL directory: {folder}")
from faster_whisper import WhisperModel
import time

print("Loading ASR model...", flush=True)

model = WhisperModel(
    "medium",
    device="cuda",
    compute_type="float16"
)
print("ASR model loaded!", flush=True)

start_time = time.perf_counter()

segments, info = model.transcribe(
    "audio/zone_c.m4a",
    language="en",
    beam_size=5
)

transcription = " ".join(
    segment.text.strip() for segment in segments
)

elapsed_time = time.perf_counter() - start_time

print("Language:", info.language)
print("Transcription:", transcription)
print(f"Transcription time: {elapsed_time:.2f} seconds")
