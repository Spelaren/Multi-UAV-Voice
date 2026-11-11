
import os
import re
import json
import time
import urllib.request
import subprocess
import sys
from pathlib import Path

# ==========================================
# 1. CUDA DLL CONFIGURATION
# ==========================================

PROJECT_DIR = Path(__file__).resolve().parent

nvidia_dir = (
    PROJECT_DIR
    / ".venv"
    / "Lib"
    / "site-packages"
    / "nvidia"
)

dll_directories = []

for folder in ["cublas", "cudnn", "cuda_nvrtc"]:
    dll_path = nvidia_dir / folder / "bin"

    if dll_path.exists():
        dll_directories.append(
            os.add_dll_directory(str(dll_path))
        )
        print(f"Added CUDA DLL directory: {folder}")


from faster_whisper import WhisperModel

from validation.validator import validate_missions
from validation.grounding import check_command_grounding

from clarification.clarification import (
    get_clarification_question,
    get_grounding_clarification_question,
    combine_command_with_clarification
)


# ==========================================
# 2. CONFIGURATION
# ==========================================

AUDIO_FILE = PROJECT_DIR / "audio" / "live_command.wav"

API_URL = "http://127.0.0.1:1234/v1/chat/completions"
MODEL = "qwen3-4b-instruct-2507"

SYSTEM_PROMPT = """
You are a command parser for a simulated multi-UAV warehouse system.

Convert spoken English commands into structured JSON.

Return ONLY a valid JSON object using this format:

{
  "missions": [
    {
      "uav_id": "1",
      "task": "inspect_zone",
      "location": "A"
    }
  ]
}

Rules:
1. Return only JSON. No explanations or markdown.
2. The top-level object must contain exactly one field: "missions".
3. "missions" must be an array of mission objects.
4. Each mission must contain exactly:
   "uav_id", "task", "location".
5. "uav_id" must be the drone number as a string.
   Example: "3", not "Drone 3".
6. Allowed task names:
   - "inspect_zone"
   - "inspect_pallet"
7. For zone inspections, use the zone letter.
   Example: "A".
8. For pallet inspections, use the pallet identifier.
   Example: "P05".
9. When multiple drones are mentioned, create one mission
   object for each drone assignment.
10. Preserve the assignments from the spoken command.
11. Never invent missing drone IDs, tasks, or locations.
12. If information is missing or unclear, use null for
    the corresponding field.
13. Do not decide whether a mission is allowed.
    A separate validator will check that.

CRITICAL SAFETY RULES:
14. Never guess or invent a zone, pallet location, or UAV ID.
15. A location must be explicitly mentioned in the user's command.
16. If the user says "inspect zone" without specifying
    a zone letter, set "location" to null.
17. If the user says "inspect pallet" without specifying
    a pallet identifier, set "location" to null.
18. Do not use default values for missing information.
19. If any required information is missing, preserve
    the missing field as null.
20. Safety is more important than completing a mission.
"""


# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================

def record_audio():
    """
    Record a voice command using the existing
    audio/record.py script.
    """

    subprocess.run(
        [
            sys.executable,
            str(PROJECT_DIR / "audio" / "record.py")
        ],
        check=True
    )

    return AUDIO_FILE


def transcribe_audio(asr_model, audio_file):
    """
    Convert recorded audio to text using Whisper.
    """

    start = time.perf_counter()

    segments, _ = asr_model.transcribe(
        str(audio_file),
        language="en",
        beam_size=5
    )

    text = " ".join(
        segment.text.strip()
        for segment in segments
    ).strip()

    elapsed = time.perf_counter() - start

    return text, elapsed


def uav_mentioned(transcription, uav_id):
    """
    Check that the SLM's UAV ID was explicitly
    present in the original transcription.
    """

    if not isinstance(uav_id, str):
        return False

    pattern = (
        rf"\b(?:DRONE|UAV)\s+"
        rf"{re.escape(uav_id)}\b"
    )

    return bool(
        re.search(pattern, transcription.upper())
    )


def record_clarification(asr_model, question):
    """
    Ask the question and record a spoken answer.

    This function does not approve any mission.
    """

    print("\n--- CLARIFICATION REQUIRED ---")
    print(question)

    print("\n--- RECORD CLARIFICATION ---")
    print("Please answer by voice.")

    clarification_file = record_audio()

    clarification_answer, clarification_time = (
        transcribe_audio(
            asr_model,
            clarification_file
        )
    )

    print("\n--- CLARIFICATION ASR RESULT ---")
    print("Clarification received:", clarification_answer)
    print(
        f"Clarification ASR time: "
        f"{clarification_time:.2f} seconds"
    )

    return clarification_answer


# ==========================================
# 4. LIVE MICROPHONE RECORDING
# ==========================================

print("\n--- LIVE VOICE COMMAND ---")

record_audio()


# ==========================================
# 5. ASR - SPEECH TO TEXT
# ==========================================

print("\nLoading ASR model...")

asr_model = WhisperModel(
    "medium",
    device="cuda",
    compute_type="float16"
)

print("ASR model loaded!")

transcription, asr_time = transcribe_audio(
    asr_model,
    AUDIO_FILE
)

print("\n--- ASR RESULT ---")
print("Transcription:", transcription)
print(f"ASR time: {asr_time:.2f} seconds")


# ==========================================
# 6. SLM - TEXT TO JSON
# ==========================================

print("\nSending command to LM Studio...")

payload = {
    "model": MODEL,
    "messages": [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": transcription
        }
    ],
    "temperature": 0,
    "stream": False
}

request = urllib.request.Request(
    API_URL,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

start_slm = time.perf_counter()

with urllib.request.urlopen(
    request,
    timeout=120
) as response:
    api_result = json.load(response)

slm_time = time.perf_counter() - start_slm

model_output = api_result["choices"][0]["message"]["content"]

print("\n--- SLM RESULT ---")
print("JSON output:", model_output)
print(f"SLM time: {slm_time:.2f} seconds")


# ==========================================
# 7. PERFORMANCE
# ==========================================

total_time = asr_time + slm_time

print("\n--- PERFORMANCE ---")
print(f"ASR processing time: {asr_time:.2f} seconds")
print(f"SLM processing time: {slm_time:.2f} seconds")
print(f"Total processing time: {total_time:.2f} seconds")


# ==========================================
# 8. SAFETY VALIDATION
# ==========================================

print("\n--- SAFETY VALIDATION ---")

valid, validation_result = validate_missions(model_output)

grounded = False
grounding_message = ""

if valid:
    grounded, grounding_message = check_command_grounding(
        transcription,
        validation_result
    )

approved = valid and grounded

if approved:
    print("Validation status: APPROVED")
    print("Validated missions:")
    print(json.dumps(validation_result, indent=2))

else:
    print("Validation status: REJECTED")

    if not valid:
        print("Reason:", validation_result)
    else:
        print("Reason:", grounding_message)

    print(
        "Mission cancelled - "
        "no command will be dispatched."
    )


# ==========================================
# 9. CLARIFICATION CHECK
# ==========================================

print("\n--- CLARIFICATION CHECK ---")

clarification_question = None
mission_data = None

try:
    mission_data = json.loads(model_output)

except (json.JSONDecodeError, TypeError):
    print("Clarification unavailable: invalid JSON.")


if not approved and isinstance(mission_data, dict):

    missions = mission_data.get("missions")

    if isinstance(missions, list) and missions:

        # Do not trust an invented UAV ID.
        # This version supports a single target
        # for the clarification demonstration.

        if len(missions) == 1 and isinstance(missions[0], dict):

            mission = missions[0]
            uav_id = mission.get("uav_id")

            if (
                isinstance(uav_id, str)
                and not uav_mentioned(transcription, uav_id)
            ):
                clarification_question = (
                    "Please repeat the full command, "
                    "including the drone number and location."
                )

            else:
                # First: check missing fields (null)
                clarification_question = (
                    get_clarification_question(mission_data)
                )

                # Second: check invalid locations
                # or failed location grounding
                if clarification_question is None:

                    reason = (
                        str(validation_result)
                        if not valid
                        else grounding_message
                    ).lower()

                    location_problem = (
                        "invalid zone" in reason
                        or "invalid pallet" in reason
                        or "zone " in reason
                        or "pallet " in reason
                    )

                    if location_problem:
                        clarification_question = (
                            get_grounding_clarification_question(
                                mission_data
                            )
                        )


# ==========================================
# 10. VOICE CLARIFICATION
# ==========================================

if clarification_question:

    clarification_answer = record_clarification(
        asr_model,
        clarification_question
    )

    combined_command = combine_command_with_clarification(
        transcription,
        clarification_answer
    )

    if combined_command:
        print("\n--- COMBINED COMMAND ---")
        print(combined_command)

        print(
            "\nClarification captured. "
            "Combined command has NOT been revalidated."
        )
    else:
        print(
            "\nClarification was empty. "
            "Original mission remains rejected."
        )

elif approved:
    print("No clarification needed.")

else:
    print(
        "No safe clarification question available. "
        "Original mission remains rejected."
    )


# ==========================================
# 11. PIPELINE COMPLETED
# ==========================================

print("\nPipeline completed.")
print("No UAV command was dispatched.")
