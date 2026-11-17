
import json
import re
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_DIR / "config" / "warehouse.json"


def validate_location_correction(
    original_command,
    clarification_answer
):
    """
    Validate a correction of an invalid pallet location.

    This function only checks correction eligibility.
    It does not authorize mission execution.
    """

    if not isinstance(original_command, str):
        return False, "Invalid original command"

    if not isinstance(clarification_answer, str):
        return False, "Invalid clarification answer"

    original = original_command.upper().strip()
    answer = clarification_answer.upper().strip()

    # Require one complete pallet inspection command.
  
    pattern = (
        r"^DRONE\s+([1-8])\s*[,.]?\s*"
        r"INSPECT\s+PALLET\s*,?\s+(P\d+)\s*[.]?$"
    )




    original_match = re.fullmatch(pattern, original)
    answer_match = re.fullmatch(pattern, answer)

    if not original_match or not answer_match:
        return False, "Correction requires complete pallet commands"

    original_uav, original_pallet = original_match.groups()
    answer_uav, answer_pallet = answer_match.groups()

    if original_uav != answer_uav:
        return False, "UAV ID cannot change during correction"

    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        warehouse = json.load(file)

    valid_pallets = warehouse["pallet_locations"]

    if original_pallet in valid_pallets:
        return False, "Original pallet is already valid"

    if answer_pallet not in valid_pallets:
        return False, "Corrected pallet is invalid"

    return True, "Valid pallet correction"
