import json
from pathlib import Path
# ==========================================
# CLARIFICATION MODULE
# ==========================================


def get_clarification_question(mission_data):
    """
    Generate clarification questions for incomplete
    or invalid mission fields.

    This function never approves a mission.
    """

    if not isinstance(mission_data, dict):
        return None

    missions = mission_data.get("missions")

    if not isinstance(missions, list) or not missions:
        return None

    # Load valid warehouse identifiers and locations.
    config_file = (
        Path(__file__).resolve().parent.parent
        / "config"
        / "warehouse.json"
    )

    try:
        with open(config_file, "r", encoding="utf-8") as file:
            warehouse = json.load(file)
    except (OSError, ValueError):
        # Fail closed: configuration errors must not
        # produce a guessed clarification.
        return None

    valid_uavs = warehouse.get("uavs", {})
    valid_zones = warehouse.get("zones", [])
    valid_pallets = warehouse.get("pallet_locations", {})
    allowed_tasks = warehouse.get("allowed_tasks", [])

    for mission in missions:

        if not isinstance(mission, dict):
            continue

        uav_id = mission.get("uav_id")
        task = mission.get("task")
        location = mission.get("location")

        # Missing or invalid UAV ID
        if (
            not isinstance(uav_id, str)
            or uav_id not in valid_uavs
        ):
            return "Which valid drone should perform the task?"

        # Missing or unsupported task
        if (
            not isinstance(task, str)
            or task not in allowed_tasks
        ):
            return f"What task should Drone {uav_id} perform?"

        # Missing or invalid zone
        if task == "inspect_zone":
            if (
                not isinstance(location, str)
                or location not in valid_zones
            ):
                return f"Which valid zone should Drone {uav_id} inspect?"

        # Missing or invalid pallet
        if task == "inspect_pallet":
            if (
                not isinstance(location, str)
                or location not in valid_pallets
            ):
                return f"Which valid pallet should Drone {uav_id} inspect?"

    return None




def get_grounding_clarification_question(
    mission_data,
    grounding_message=None
):
    """
    Ask for the specific information that failed grounding.

    This function only generates a question.
    It never validates or authorizes a mission.
    """

    if not isinstance(mission_data, dict):
        return None

    missions = mission_data.get("missions")

    if not isinstance(missions, list) or not missions:
        return None

    message = str(grounding_message or "").lower()

    # UAV identity was not explicitly grounded
    if "uav" in message or "drone" in message:
        return "Which drone should perform the task?"

    # Location was not explicitly grounded
    if "zone" in message or "pallet" in message or "location" in message:

        for mission in missions:
            if not isinstance(mission, dict):
                continue

            uav_id = mission.get("uav_id")
            task = mission.get("task")

            if not isinstance(uav_id, str):
                return "Which drone should perform the task?"

            if task == "inspect_zone":
                return f"Which zone should Drone {uav_id} inspect?"

            if task == "inspect_pallet":
                return f"Which pallet should Drone {uav_id} inspect?"

    # Never guess which information was incorrect
    return "Please repeat the complete command with the drone and location."


def combine_command_with_clarification(
    original_command,
    clarification_answer
):
    """
    Combine the original voice command with the
    user's clarification answer.

    The combined text must be processed again
    by the SLM and safety validation.
    """

    if not isinstance(original_command, str):
        return None

    if not isinstance(clarification_answer, str):
        return None

    original_command = original_command.strip()
    clarification_answer = clarification_answer.strip()

    if not original_command or not clarification_answer:
        return None

    return (
        f"{original_command}\n"
        f"Clarification from user: {clarification_answer}"
    )


# ==========================================
# STANDALONE TEST
# ==========================================

if __name__ == "__main__":

    test_data = {
        "missions": [
            {
                "uav_id": "2",
                "task": "inspect_zone",
                "location": None
            }
        ]
    }

    question = get_clarification_question(test_data)

    if question:
        print("Clarification needed:")
        print(question)
    else:
        print("No clarification needed.")
