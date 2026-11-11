
import re


def check_command_grounding(transcription, mission_data):
    """
    Check whether each mission's UAV ID and location
    are supported by the ASR transcription.

    Returns:
        (True, message) if all checks pass.
        (False, error_message) otherwise.
    """

    if not isinstance(transcription, str):
        return False, "Invalid transcription"

    if not isinstance(mission_data, dict):
        return False, "Invalid mission data"

    text = transcription.upper()

    missions = mission_data.get("missions", [])

    if not isinstance(missions, list) or not missions:
        return False, "No missions to verify"

    for index, mission in enumerate(missions, start=1):

        if not isinstance(mission, dict):
            return False, f"Mission {index}: invalid mission"

        uav_id = mission.get("uav_id")
        task = mission.get("task")
        location = mission.get("location")

        # ======================================
        # 1. UAV ID GROUNDING
        # ======================================

        if not isinstance(uav_id, str):
            return False, f"Mission {index}: missing UAV ID"

        # Require an explicit UAV reference.
        # Examples: "Drone 2", "UAV 2"
        uav_pattern = (
            rf"\b(?:DRONE|UAV)\s+"
            rf"{re.escape(uav_id)}\b"
        )

        if not re.search(uav_pattern, text):
            return (
                False,
                f"Mission {index}: UAV {uav_id} "
                "was not mentioned in the command"
            )

        # ======================================
        # 2. LOCATION GROUNDING
        # ======================================

        if task == "inspect_zone":

            if not isinstance(location, str):
                return False, f"Mission {index}: missing zone"

            zone_pattern = (
                rf"\bZONE\s+"
                rf"{re.escape(location.upper())}\b"
            )

            if not re.search(zone_pattern, text):
                return (
                    False,
                    f"Mission {index}: zone {location} "
                    "was not mentioned in the command"
                )

        elif task == "inspect_pallet":

            if not isinstance(location, str):
                return False, f"Mission {index}: missing pallet location"

            pallet_pattern = (
                rf"\b{re.escape(location.upper())}\b"
            )

            if not re.search(pallet_pattern, text):
                return (
                    False,
                    f"Mission {index}: pallet {location} "
                    "was not mentioned in the command"
                )

    return True, "UAV IDs and locations supported by transcription"


# ==========================================
# STANDALONE TEST
# ==========================================

if __name__ == "__main__":

    transcription = "Run to Inspect Zone"

    model_output = {
        "missions": [
            {
                "uav_id": "1",
                "task": "inspect_zone",
                "location": "A"
            }
        ]
    }

    valid, message = check_command_grounding(
        transcription,
        model_output
    )

    print("Grounding result:", valid)
    print("Details:", message)
