
import os
import time
from pathlib import Path

from Audio.normalization import normalize_pallet_identifiers

PROJECT_DIR = Path(__file__).resolve().parent.parent

# Keep CUDA DLL directory handles alive
dll_directories = []

nvidia_dir = (
    PROJECT_DIR
    / ".venv"
    / "Lib"
    / "site-packages"
    / "nvidia"
)

for folder in ["cublas", "cudnn", "cuda_nvrtc"]:
    dll_path = nvidia_dir / folder / "bin"

    if dll_path.exists() and hasattr(os, "add_dll_directory"):
        dll_directories.append(
            os.add_dll_directory(str(dll_path))
        )

from faster_whisper import WhisperModel


class ASREngine:
    def __init__(self):
        self.model = None

    def load_model(self):
        """
        Load Whisper only when explicitly requested.
        """
        if self.model is None:
            self.model = WhisperModel(
                "medium",
                device="cuda",
                compute_type="float16"
            )

        return True

    def transcribe(self, audio_file):
        """
        Transcribe an existing audio file.
        Does not start microphone recording.
        """
        if self.model is None:
            raise RuntimeError("ASR model is not loaded")

        start = time.perf_counter()

        segments, _ = self.model.transcribe(
            str(audio_file),
            language="en",
            beam_size=5
        )

        transcription = " ".join(
            segment.text.strip()
            for segment in segments
        ).strip()

        transcription = normalize_pallet_identifiers(
            transcription
        )


        elapsed = time.perf_counter() - start

        return transcription, elapsed
