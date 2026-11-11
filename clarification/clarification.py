
# ==========================================
# CLARIFICATION MODULE
# ==========================================

def get_clarification_question(mission_data):
    """
    Check whether a mission is missing required information.

    Returns:
        str: A clarification question if information is missing.
        None: If no clarification is needed.
    """

    if not isinstance(mission_data, dict):
        return None

    missions = mission_data.get("missions")

    if not isinstance(missions, list):
        return None

    for mission in missions:

        if not isinstance(mission, dict):
            continue

        uav_id = mission.get("uav_id")
        task = mission.get("task")
        location = mission.get("location")

        # Missing UAV DD
        if uav_id is None:
            return "Which drone should perform the task?"

        # Missing task
        if task is None:
            return f"What should Drone {uav_id} do?"

        # Missing location
        if location is None:

            if task == "inspect_zone":
                return (
                    f"Which zone should Drone {uav_id} inspect?"
                )

            if task == "inspect_pallet":
                return (
                    f"Which pallet should Drone {uav_id} inspect?"
                )

    return None




def get_grounding_clarification_question(mission_data):
    """
    Generate a clarification question when a mission
    has failed the grounding check.

    This function does not approve any mission.
    """

    if not isinstance(mission_data, dict):
        return None

    missions = mission_data.get("missions")

    if not isinstance(missions, list):
        return None

    for mission in missions:
        if not isinstance(mission, dict):
            continue

        uav_id = mission.get("uav_id")
        task = mission.get("task")

        if not isinstance(uav_id, str):
            continue

        if task == "inspect_zone":
            return f"Which zone should Drone {uav_id} inspect?"

        if task == "inspect_pallet":
            return f"Which pallet should Drone {uav_id} inspect?"

    return None



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
