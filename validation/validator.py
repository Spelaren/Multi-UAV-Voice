
import json
from pathlib import Path

# Load simulated warehouse configuration
PROJECT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_DIR / "config" / "warehouse.json"


def validate_missions(model_output):
    """
    Validate JSON missions against warehouse configuration.

    Returns:
        (True, validated_data) if all missions are valid.
        (False, error_message) otherwise.
    """

    # Step 1: Parse JSON
    try:
        data = json.loads(model_output)
    except (json.JSONDecodeError, TypeError):
        return False, "Invalid JSON format"

    # Step 2: Load warehouse configuration
    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        warehouse = json.load(file)

    # Step 3: Validate top-level structure
    if not isinstance(data, dict):
        return False, "JSON root must be an object"

    if set(data.keys()) != {"missions"}:
        return False, "JSON must contain exactly the 'missions' field"

    missions = data["missions"]

    if not isinstance(missions, list) or not missions:
        return False, "Missions must be a non-empty list"

    # Step 4: Validate each mission
    used_uavs = set()

    for index, mission in enumerate(missions, start=1):

        if not isinstance(mission, dict):
            return False, f"Mission {index}: must be an object"

        required_fields = {"uav_id", "task", "location"}

        if set(mission.keys()) != required_fields:
            return False, f"Mission {index}: incorrect fields"

        uav_id = mission["uav_id"]
        task = mission["task"]
        location = mission["location"]

        # Check types
        if not all(
            isinstance(value, str)
            for value in [uav_id, task, location]
        ):
            return False, f"Mission {index}: fields must be strings"

        # Check UAV ID
        if uav_id not in warehouse["uavs"]:
            return False, f"Mission {index}: unknown UAV {uav_id}"

        # Prevent duplicate UAV assignments
        if uav_id in used_uavs:
            return False, f"Mission {index}: duplicate UAV {uav_id}"

        used_uavs.add(uav_id)

        # Check allowed task
        if task not in warehouse["allowed_tasks"]:
            return False, f"Mission {index}: task not allowed"

        # Check location according to task
        if task == "inspect_zone":
            if location not in warehouse["zones"]:
                return False, f"Mission {index}: invalid zone {location}"

        elif task == "inspect_pallet":
            if location not in warehouse["pallet_locations"]:
                return False, f"Mission {index}: invalid pallet {location}"

        else:
            return False, f"Mission {index}: unsupported task"

    # All missions passed validation
    return True, data


# Standalone test
if __name__ == "__main__":

    test_command = """
    {
      "missions": [
        {
          "uav_id": "99",
          "task": "inspect_zone",
          "location": "A"
        },
        {
          "uav_id": "2",
          "task": "inspect_pallet",
          "location": "P05"
        }
      ]
    }
    """

    valid, result = validate_missions(test_command)

    print("Validation result:", valid)
    print("Details:", result)
