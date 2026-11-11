from slm.slm_engine import SLMEngine
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from datetime import datetime
import threading
import importlib.util
from slm.slm_engine import SLMEngine

from validation.validator import validate_missions
from validation.grounding import check_command_grounding

import numpy as np
import sounddevice as sd
import soundfile as sf


# ==========================================
# CONFIGURATION
# ==========================================

PROJECT_DIR = Path(__file__).resolve().parent
AUDIO_FILE = PROJECT_DIR / "audio" / "live_command.wav"
SAMPLE_RATE = 16000

BG = "#0F172A"
PANEL = "#1E293B"
INPUT_BG = "#111827"
TEXT = "#F8FAFC"
MUTED = "#94A3B8"
BLUE = "#2563EB"
RED = "#DC2626"
GREEN = "#22C55E"
BORDER = "#334155"


# ==========================================
# ASR IMPORT
# ==========================================

# Keep the working file-based import for now.

ASR_MODULE_PATH = PROJECT_DIR / "audio" / "asr_engine.py"

spec = importlib.util.spec_from_file_location(
    "asr_engine",
    ASR_MODULE_PATH
)

if spec is None or spec.loader is None:
    raise ImportError("Could not load ASR engine")

asr_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asr_module)

ASREngine = asr_module.ASREngine


# ==========================================
# MAIN APPLICATION
# ==========================================

class SLMApp:

    def __init__(self, root):

        self.root = root
        self.root.title("SLM - Multi-UAV Voice Control")

        # Compact window that can be resized
        self.root.geometry("940x700")
        self.root.minsize(760, 590)
        self.root.configure(bg=BG)

        self.recording = False
        self.processing = False
        self.current_transcription = ""

        self.audio_stream = None
        self.audio_frames = []

        self.asr_engine = ASREngine()
        self.slm_engine = SLMEngine()

        self.clarification_attempts = 0

        # Used to ignore outdated ASR results
        self.command_version = 0
        self.cancelled = False

        self.build_interface()

        self.log("Application initialized")
        self.log("System idle - awaiting user command")
        self.log("Safety validation awaiting command")
        self.log("No UAV mission authorized")

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.close_app
        )

    # ======================================
    # UI HELPERS
    # ======================================

    def make_label(
        self,
        parent,
        text,
        size=10,
        color=TEXT,
        bold=False
    ):

        return tk.Label(
            parent,
            text=text,
            bg=parent.cget("bg"),
            fg=color,
            font=(
                "Segoe UI",
                size,
                "bold" if bold else "normal"
            ),
            anchor="w"
        )

    def make_panel(self, parent):

        return tk.Frame(
            parent,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=13,
            pady=9
        )

    def make_button(
        self,
        parent,
        text,
        command,
        color=BLUE
    ):

        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg="white",
            disabledforeground=MUTED,
            activebackground=color,
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            padx=15,
            pady=7,
            cursor="hand2"
        )

    # ======================================
    # COMPACT RESPONSIVE INTERFACE
    # ======================================

    def build_interface(self):

        container = tk.Frame(
            self.root,
            bg=BG,
            padx=15,
            pady=12
        )

        container.pack(
            fill="both",
            expand=True
        )

        # Only the log row grows vertically
        container.grid_columnconfigure(
            0,
            weight=1
        )

        container.grid_rowconfigure(
            5,
            weight=1,
            minsize=105
        )

        # ----------------------------------
        # HEADER - ROW 0
        # ----------------------------------

        header = tk.Frame(container, bg=BG)

        header.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 9)
        )

        self.make_label(
            header,
            "SLM CONTROL CENTER",
            19,
            TEXT,
            True
        ).pack(anchor="w")

        self.make_label(
            header,
            "MULTI-UAV VOICE COMMAND SYSTEM",
            9,
            MUTED
        ).pack(anchor="w")

        # ----------------------------------
        # SYSTEM STATUS - ROW 1
        # ----------------------------------

        status_panel = self.make_panel(container)

        status_panel.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 8)
        )

        self.make_label(
            status_panel,
            "SYSTEM STATUS",
            9,
            MUTED,
            True
        ).pack(anchor="w")

        self.status_label = self.make_label(
            status_panel,
            "IDLE - AWAITING COMMAND",
            12,
            TEXT,
            True
        )

        self.status_label.pack(
            anchor="w",
            pady=(3, 0)
        )

        # ----------------------------------
        # ENGINE STATUS - ROW 2
        # ----------------------------------

        engines = tk.Frame(container, bg=BG)

        engines.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(0, 8)
        )

        engines.grid_columnconfigure(
            0,
            weight=1,
            uniform="engines"
        )

        engines.grid_columnconfigure(
            1,
            weight=1,
            uniform="engines"
        )

        asr_panel = self.make_panel(engines)

        asr_panel.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 4)
        )

        self.make_label(
            asr_panel,
            "ASR ENGINE",
            9,
            MUTED,
            True
        ).pack(anchor="w")

        self.make_label(
            asr_panel,
            "Whisper Medium",
            11,
            TEXT,
            True
        ).pack(anchor="w", pady=(2, 0))

        self.asr_status_label = self.make_label(
            asr_panel,
            "Not initialized",
            9,
            MUTED
        )

        self.asr_status_label.pack(anchor="w")

        slm_panel = self.make_panel(engines)

        slm_panel.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(4, 0)
        )

        self.make_label(
            slm_panel,
            "LANGUAGE MODEL",
            9,
            MUTED,
            True
        ).pack(anchor="w")

        self.make_label(
            slm_panel,
            "Qwen3-4B",
            11,
            TEXT,
            True
        ).pack(anchor="w", pady=(2, 0))

        self.slm_status_label = self.make_label(
            slm_panel,
            "Not connected",
            9,
            MUTED
        )

        self.slm_status_label.pack(anchor="w")

        # ----------------------------------
        # VOICE COMMAND - ROW 3
        # ----------------------------------

        voice_panel = self.make_panel(container)

        voice_panel.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(0, 8)
        )

        self.make_label(
            voice_panel,
            "VOICE COMMAND",
            11,
            TEXT,
            True
        ).pack(anchor="w")

        self.voice_status = self.make_label(
            voice_panel,
            "Microphone ready - no recording active",
            9,
            MUTED
        )

        self.voice_status.pack(
            anchor="w",
            pady=(4, 7)
        )

        controls = tk.Frame(voice_panel, bg=PANEL)

        controls.pack(
            fill="x"
        )

        self.start_button = self.make_button(
            controls,
            "Start Recording",
            self.start_recording,
            BLUE
        )

        self.start_button.pack(
            side="left",
            padx=(0, 8)
        )

        self.stop_button = self.make_button(
            controls,
            "Stop Recording",
            self.stop_recording,
            RED
        )

        self.stop_button.pack(side="left")

        self.stop_button.configure(
            state="disabled"
        )

        # ----------------------------------
        # MISSION REVIEW - ROW 4
        # ----------------------------------

        mission_panel = self.make_panel(container)

        mission_panel.grid(
            row=4,
            column=0,
            sticky="ew",
            pady=(0, 8)
        )

        self.make_label(
            mission_panel,
            "MISSION REVIEW",
            11,
            TEXT,
            True
        ).pack(anchor="w")

        self.mission_label = self.make_label(
            mission_panel,
            "UAV: --     Task: --     Location: --",
            10,
            MUTED
        )

        self.mission_label.pack(
            anchor="w",
            pady=(5, 2)
        )

        self.validation_label = self.make_label(
            mission_panel,
            "Safety validation: Awaiting command",
            9,
            MUTED
        )

        self.validation_label.pack(anchor="w")

        self.clarification_label = self.make_label(
            mission_panel,
            "Clarification attempts: 0 / 2",
            9,
            MUTED
        )

        self.clarification_label.pack(
            anchor="w",
            pady=(2, 0)
        )

        # ----------------------------------
        # SAFETY LOG - ROW 5
        # ----------------------------------

        log_panel = self.make_panel(container)

        log_panel.grid(
            row=5,
            column=0,
            sticky="nsew",
            pady=(0, 8)
        )

        log_panel.grid_columnconfigure(
            0,
            weight=1
        )

        log_panel.grid_rowconfigure(
            1,
            weight=1
        )

        self.make_label(
            log_panel,
            "SAFETY LOG",
            11,
            TEXT,
            True
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 6)
        )

        log_content = tk.Frame(
            log_panel,
            bg=INPUT_BG
        )

        log_content.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        log_content.grid_rowconfigure(
            0,
            weight=1
        )

        log_content.grid_columnconfigure(
            0,
            weight=1
        )

        self.log_box = tk.Text(
            log_content,
            height=4,
            bg=INPUT_BG,
            fg="#CBD5E1",
            insertbackground=TEXT,
            font=("Consolas", 9),
            relief="flat",
            padx=8,
            pady=6,
            wrap="word",
            state="disabled"
        )

        self.log_box.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        scrollbar = tk.Scrollbar(
            log_content,
            command=self.log_box.yview
        )

        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        self.log_box.configure(
            yscrollcommand=scrollbar.set
        )

        # ----------------------------------
        # ACTION BUTTONS - ROW 6
        # ----------------------------------

        actions = tk.Frame(container, bg=BG)

        actions.grid(
            row=6,
            column=0,
            sticky="ew"
        )

        self.send_button = self.make_button(
            actions,
            "Confirm & Send Mission",
            self.send_mission,
            BLUE
        )

        self.send_button.pack(
            side="left",
            padx=(0, 8)
        )

        self.send_button.configure(
            state="disabled"
        )

        self.cancel_button = self.make_button(
            actions,
            "Cancel Mission",
            self.cancel_mission,
            RED
        )

        self.cancel_button.pack(side="left")

    # ======================================
    # SAFETY LOG
    # ======================================

    def log(self, message):

        timestamp = datetime.now().strftime(
            "%H:%M:%S"
        )

        self.log_box.configure(state="normal")

        self.log_box.insert(
            "end",
            f"[{timestamp}] {message}\n"
        )

        self.log_box.see("end")

        self.log_box.configure(state="disabled")

    # ======================================
    # RESET MISSION STATE
    # ======================================

    def reset_mission_state(self):

        self.send_button.configure(state="disabled")

        self.mission_label.configure(
            text="UAV: --     Task: --     Location: --",
            fg=MUTED
        )

        self.validation_label.configure(
            text="Safety validation: Awaiting command",
            fg=MUTED
        )

        self.clarification_attempts = 0

        self.clarification_label.configure(
            text="Clarification attempts: 0 / 2"
        )

    # ======================================
    # MICROPHONE RECORDING
    # ======================================

    def audio_callback(
        self,
        indata,
        frames,
        time_info,
        status
    ):

        if status:
            print("Audio status:", status)

        if self.recording:
            self.audio_frames.append(
                indata.copy()
            )

    def start_recording(self):

        if self.recording or self.processing:
            return

        self.command_version += 1
        self.cancelled = False

        self.reset_mission_state()

        try:
            self.audio_frames = []

            self.audio_stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
                callback=self.audio_callback
            )

            self.recording = True
            self.audio_stream.start()

            self.status_label.configure(
                text="RECORDING",
                fg=RED
            )

            self.voice_status.configure(
                text="Microphone active - speak your command",
                fg=MUTED
            )

            self.start_button.configure(
                state="disabled"
            )

            self.stop_button.configure(
                state="normal"
            )

            self.log("Voice recording started manually")

        except Exception as error:

            self.recording = False

            if self.audio_stream is not None:
                self.audio_stream.close()
                self.audio_stream = None

            self.start_button.configure(
                state="normal"
            )

            self.stop_button.configure(
                state="disabled"
            )

            self.status_label.configure(
                text="MICROPHONE ERROR",
                fg=RED
            )

            self.log(f"Microphone error: {error}")

            messagebox.showerror(
                "Microphone Error",
                str(error)
            )

    def stop_recording(self):

        if not self.recording:
            return

        self.recording = False

        try:
            if self.audio_stream is not None:
                self.audio_stream.stop()
                self.audio_stream.close()
                self.audio_stream = None

            self.stop_button.configure(
                state="disabled"
            )

            if not self.audio_frames:
                raise ValueError("No audio captured")

            audio_data = np.concatenate(
                self.audio_frames,
                axis=0
            )

            AUDIO_FILE.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            sf.write(
                str(AUDIO_FILE),
                audio_data,
                SAMPLE_RATE
            )

            self.status_label.configure(
                text="AUDIO SAVED",
                fg=GREEN
            )

            self.log("Voice recording stopped")
            self.log("Audio saved successfully")

            self.process_audio()

        except Exception as error:

            self.status_label.configure(
                text="RECORDING ERROR",
                fg=RED
            )

            self.start_button.configure(
                state="normal"
            )

            self.stop_button.configure(
                state="disabled"
            )

            self.log(f"Recording error: {error}")

            messagebox.showerror(
                "Recording Error",
                str(error)
            )

    # ======================================
    # ASR PROCESSING
    # ======================================

    def process_audio(self):

        if self.processing:
            return

        self.processing = True

        version = self.command_version

        self.status_label.configure(
            text="PROCESSING AUDIO",
            fg=BLUE
        )

        self.asr_status_label.configure(
            text="Processing...",
            fg=BLUE
        )

        self.start_button.configure(
            state="disabled"
        )

        self.stop_button.configure(
            state="disabled"
        )

        self.send_button.configure(
            state="disabled"
        )

        self.log("ASR processing started")

        threading.Thread(
            target=self.asr_worker,
            args=(version,),
            daemon=True
        ).start()

    def asr_worker(self, version):

        try:
            self.asr_engine.load_model()

            transcription, asr_time = (
                self.asr_engine.transcribe(
                    AUDIO_FILE
                )
            )

            self.root.after(
                0,
                self.asr_completed,
                version,
                transcription,
                asr_time
            )

        except Exception as error:

            error_message = str(error)

            self.root.after(
                0,
                self.asr_failed,
                version,
                error_message
            )

    def asr_completed(
        self,
        version,
        transcription,
        asr_time
    ):

        self.processing = False

        # Ignore results from cancelled commands.
        if (
            version != self.command_version
            or self.cancelled
        ):
            self.start_button.configure(
                state="normal"
            )

            self.log("Cancelled ASR result ignored")
            return

        self.status_label.configure(
            text="TRANSCRIPTION COMPLETED",
            fg=GREEN
        )

        self.asr_status_label.configure(
            text="Ready",
            fg=GREEN
        )

        self.voice_status.configure(
            text=f"Recognized: {transcription}",
            fg=TEXT
        )

        self.start_button.configure(
            state="normal"
        )

        self.log(
            f"ASR transcription: {transcription}"
        )

        self.log(
            f"ASR processing time: {asr_time:.2f} s"
        )

        self.log("No UAV mission dispatched")
        self.process_slm(transcription, version)
        self.current_transcription = transcription
     
    # ======================================
    # SLM PROCESSING
    # ======================================

    def process_slm(self, transcription, version):
        """
        Interpret the transcription using Qwen3-4B.
        Run outside the Tkinter main thread.
        """

        self.processing = True

        self.status_label.configure(
            text="INTERPRETING COMMAND",
            fg=BLUE
        )

        self.slm_status_label.configure(
            text="Processing...",
            fg=BLUE
        )

        self.start_button.configure(state="disabled")
        self.send_button.configure(state="disabled")

        self.log("SLM processing started")

        threading.Thread(
            target=self.slm_worker,
            args=(transcription, version),
            daemon=True
        ).start()

    def slm_worker(self, transcription, version):

        try:
            model_output, slm_time = (
                self.slm_engine.parse_command(
                    transcription
                )
            )

            self.root.after(
                0,
                self.slm_completed,
                version,
                model_output,
                slm_time
            )

        except Exception as error:

            self.root.after(
                0,
                self.slm_failed,
                version,
                str(error)
            )

  
    def slm_completed(
        self,
        version,
        model_output,
        slm_time
    ):
        """
        Validate the SLM output before displaying
        any mission as approved.
        """

        # Ignore outdated or cancelled commands
        if (
            version != self.command_version
            or self.cancelled
        ):
            self.processing = False
            self.start_button.configure(state="normal")
            self.log("Cancelled SLM result ignored")
            return

        self.processing = False

        self.slm_status_label.configure(
            text="Connected",
            fg=GREEN
        )

        self.log(f"SLM processing time: {slm_time:.2f} s")
        self.log(f"SLM output: {model_output}")

        # A new SLM result must never inherit
        # approval from a previous command.
        self.send_button.configure(state="disabled")

        self.mission_label.configure(
            text="UAV: --     Task: --     Location: --",
            fg=MUTED
        )

        # ==================================
        # STEP 1: WAREHOUSE VALIDATION
        # ==================================

        valid, validation_result = validate_missions(
            model_output
        )

        if not valid:
            self.status_label.configure(
                text="MISSION REJECTED",
                fg=RED
            )

            self.validation_label.configure(
                text="Safety validation: REJECTED",
                fg=RED
            )

            self.log(
                f"Warehouse validation failed: "
                f"{validation_result}"
            )

            self.log("No UAV command dispatched")
            self.start_button.configure(state="normal")
            return

        # ==================================
        # STEP 2: GROUNDING VALIDATION
        # ==================================

        grounded, grounding_message = (
            check_command_grounding(
                self.current_transcription,
                validation_result
            )
        )

        if not grounded:
            self.status_label.configure(
                text="MISSION REJECTED",
                fg=RED
            )

            self.validation_label.configure(
                text="Safety validation: REJECTED",
                fg=RED
            )

            self.log(
                f"Grounding validation failed: "
                f"{grounding_message}"
            )

            self.log("No UAV command dispatched")
            self.start_button.configure(state="normal")
            return

        # ==================================
        # STEP 3: VALIDATED MISSION
        # ==================================

        missions = validation_result["missions"]

        mission_summary = " | ".join(
            (
                f"UAV {mission['uav_id']}: "
                f"{mission['task']} "
                f"{mission['location']}"
            )
            for mission in missions
        )

        self.mission_label.configure(
            text=mission_summary,
            fg=TEXT
        )

        self.validation_label.configure(
            text="Safety validation: APPROVED",
            fg=GREEN
        )

        self.status_label.configure(
            text="MISSION VALIDATED - AWAITING CONFIRMATION",
            fg=GREEN
        )

        self.log("Warehouse validation: PASSED")
        self.log("Grounding validation: PASSED")
        self.log("Mission validated successfully")

        # IMPORTANT:
        # Dispatch is NOT implemented.
        # Keep the send button disabled.
        self.send_button.configure(state="disabled")
        self.start_button.configure(state="normal")

        self.log("No UAV command dispatched")


        if (
            version != self.command_version
            or self.cancelled
        ):
            self.processing = False
            self.start_button.configure(state="normal")
            self.log("Cancelled SLM result ignored")
            return

        self.processing = False

        self.status_label.configure(
            text="SLM INTERPRETATION COMPLETED",
            fg=GREEN
        )

        self.slm_status_label.configure(
            text="Connected",
            fg=GREEN
        )

        self.start_button.configure(state="normal")

        self.log(f"SLM output: {model_output}")
        self.log(f"SLM processing time: {slm_time:.2f} s")
        
        # Validate the SLM output against warehouse rules
        self.send_button.configure(state="disabled")

        try:
            valid, result = validate_missions(model_output)

        except Exception as error:
            valid = False
            result = f"Validation system error: {error}"

        if valid:
            self.validation_label.configure(
                text="Warehouse validation: PASSED",
                fg=GREEN
            )

            self.status_label.configure(
                text="WAREHOUSE VALIDATED - GROUNDING PENDING",
                fg=BLUE
            )

            self.log("Warehouse validation: PASSED")
            self.log("Grounding validation: NOT YET PERFORMED")

        else:
            self.validation_label.configure(
                text="Warehouse validation: REJECTED",
                fg=RED
            )

            self.status_label.configure(
                text="MISSION REJECTED",
                fg=RED
            )

            self.log(f"Warehouse validation: REJECTED - {result}")

        self.log("No UAV command dispatched")


    def slm_failed(
        self,
        version,
        error_message
    ):

        self.processing = False

        if (
            version != self.command_version
            or self.cancelled
        ):
            self.start_button.configure(state="normal")
            return

        self.status_label.configure(
            text="SLM ERROR",
            fg=RED
        )

        self.slm_status_label.configure(
            text="Connection or processing error",
            fg=RED
        )

        self.start_button.configure(state="normal")
        self.send_button.configure(state="disabled")

        self.log(f"SLM failed: {error_message}")

        messagebox.showerror(
            "SLM Error",
            error_message
        )

    def asr_failed(
        self,
        version,
        error_message
    ):

        self.processing = False

        if (
            version != self.command_version
            or self.cancelled
        ):
            self.start_button.configure(
                state="normal"
            )
            return

        self.status_label.configure(
            text="ASR ERROR",
            fg=RED
        )

        self.asr_status_label.configure(
            text="Error",
            fg=RED
        )

        self.start_button.configure(
            state="normal"
        )

        self.send_button.configure(
            state="disabled"
        )

        self.log(f"ASR failed: {error_message}")

        messagebox.showerror(
            "ASR Error",
            error_message
        )

    # ======================================
    # MISSION CONTROL
    # ======================================

    def send_mission(self):
        # No dispatch adapter is integrated.
        # This remains disabled.
        return

    def cancel_mission(self):

        self.command_version += 1
        self.cancelled = True

        if self.recording:
            self.recording = False

            if self.audio_stream is not None:
                try:
                    self.audio_stream.stop()
                    self.audio_stream.close()
                finally:
                    self.audio_stream = None

        self.audio_frames = []

        self.reset_mission_state()

        self.status_label.configure(
            text="IDLE - AWAITING COMMAND",
            fg=TEXT
        )

        self.voice_status.configure(
            text="No recording active",
            fg=MUTED
        )

        self.stop_button.configure(
            state="disabled"
        )

        # If ASR is still running, wait until
        # it finishes before allowing new audio.
        self.start_button.configure(
            state="disabled" if self.processing else "normal"
        )

        self.log("Mission cancelled by user")
        self.log("No UAV command dispatched")

    # ======================================
    # CLOSE APPLICATION
    # ======================================

    def close_app(self):

        self.cancelled = True
        self.command_version += 1
        self.recording = False

        if self.audio_stream is not None:
            try:
                self.audio_stream.stop()
                self.audio_stream.close()
            finally:
                self.audio_stream = None

        self.root.destroy()


# ==========================================
# APPLICATION ENTRY POINT
# ==========================================

if __name__ == "__main__":

    root = tk.Tk()
    app = SLMApp(root)
    root.mainloop()
