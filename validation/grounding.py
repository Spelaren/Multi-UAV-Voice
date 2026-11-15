
import re



def check_command_grounding(transcription, mission_data):
    """
    Verify UAV, task and location evidence.

    Supports clarification answers without allowing
    conflicting UAV-to-location assignments.

    Conservative rule: reject ambiguous evidence.
    No UAV dispatch is performed here.
    """

    if not isinstance(transcription, str):
        return False, "Invalid transcription"

    if not isinstance(mission_data, dict):
        return False, "Invalid mission data"

    missions = mission_data.get("missions")

    if not isinstance(missions, list) or not missions:
        return False, "No missions to verify"

    # ======================================
    # 1. SEPARATE COMMAND AND CLARIFICATION
    # ======================================

    delimiter = "Clarification from user:"

    if transcription.lower().count(delimiter.lower()) > 1:
        return False, "Multiple clarification sections detected"

    parts = re.split(
        re.escape(delimiter),
        transcription,
        flags=re.IGNORECASE
    )

    parts = [part.upper().strip() for part in parts]

    if any(not part for part in parts):
        return False, "Empty command or clarification"

    # Reject explicit negations and cancellation wording.
    for part in parts:

       if re.search(
            r"\b(?:NOT|DON'T|DO NOT|NEVER|CANCEL|STOP|NO|AVOID)\b",
            part
        ):
            return False, "Negated or cancelled command"





       
    
   
    # Reject questions, including when ASR
    # omits the question mark.
    for part in parts:
        if (
            "?" in part
            or re.search(
                r"\b(?:CAN|COULD|WOULD|WILL)\s+YOU\b",
                part
            )
            or re.search(
                r"\bIS\s+IT\s+POSSIBLE\s+TO\b",
                part
            )
        ):
            return False, "Question detected - command not authorized"

 
   


    # ======================================
    # 2. EXTRACT EXPLICIT EVIDENCE
    # ======================================

    evidence = {}
    unassigned_parts = []

    for part in parts:

        # Detect UAV references, including invalid IDs.
        all_uavs = list(
            re.finditer(
                r"\b(?:DRONE|UAV)\s+([A-Z0-9]+)\b",
                part
            )
        )

        if not all_uavs:
            unassigned_parts.append(part)
            continue

        ids_in_part = [m.group(1) for m in all_uavs]

        # Repeating a UAV inside the same command part
        # remains ambiguous.
        if len(ids_in_part) != len(set(ids_in_part)):
            return (
                False,
                "Repeated UAV reference within one command"
            )

        for i, match in enumerate(all_uavs):

            uav_id = match.group(1)

            if not re.fullmatch(r"[1-8]", uav_id):
                return False, f"Invalid UAV reference: {uav_id}"

            end = (
                all_uavs[i + 1].start()
                if i + 1 < len(all_uavs)
                else len(part)
            )

            segment = part[match.start():end]

            evidence.setdefault(uav_id, []).append(segment)

    if not evidence:
        return False, "No explicit UAV reference found"

    # ======================================
    # 3. HANDLE UNASSIGNED CLARIFICATION
    # ======================================

    # Example:
    # Original: Inspect Zone B
    # Answer: Drone 1
    #
    # Or:
    # Original: Drone 1
    # Answer: Inspect Zone B
    #
    # Unassigned task/location text is only usable
    # when exactly one UAV is explicitly identified.

    if unassigned_parts:

        if len(evidence) != 1:
            return (
                False,
                "Task or location cannot be linked "
                "to a unique UAV"
            )

        only_uav = next(iter(evidence))
        evidence[only_uav].extend(unassigned_parts)

    # ======================================
    # 4. CHECK MISSION COVERAGE
    # ======================================

    mission_ids = []

    for index, mission in enumerate(missions, start=1):

        if not isinstance(mission, dict):
            return False, f"Mission {index}: invalid mission"

        uav_id = mission.get("uav_id")
        task = mission.get("task")
        location = mission.get("location")

        if not all(
            isinstance(value, str)
            for value in (uav_id, task, location)
        ):
            return False, f"Mission {index}: invalid fields"

        mission_ids.append(uav_id)

    if len(mission_ids) != len(set(mission_ids)):
        return False, "Duplicate UAV mission"

    if set(mission_ids) != set(evidence):
        return (
            False,
            "UAV references do not match mission assignments"
        )

    # ======================================
    # 5. VERIFY UAV-TASK-LOCATION ASSOCIATIONS
    # ======================================

    for index, mission in enumerate(missions, start=1):

        uav_id = mission["uav_id"]
        task = mission["task"]
        location = mission["location"].upper()

        segments = evidence[uav_id]

        # Collect all explicitly mentioned locations.
        zones = set()
        pallets = set()
        has_inspect = False

        for segment in segments:

            zones.update(
                re.findall(r"\bZONE\s+([A-Z])\b", segment)
            )

            pallets.update(
                re.findall(r"\bP\d{2}\b", segment)
            )

            if re.search(r"\bINSPECT\b", segment):
                has_inspect = True

        if not has_inspect:
            return (
                False,
                f"Mission {index}: inspect task not grounded"
            )

        if task == "inspect_zone":

            if pallets or zones != {location}:
                return (
                    False,
                    f"Mission {index}: conflicting or "
                    f"missing zone assignment for UAV {uav_id}"
                )

        elif task == "inspect_pallet":

            if zones or pallets != {location}:
                return (
                    False,
                    f"Mission {index}: conflicting or "
                    f"missing pallet assignment for UAV {uav_id}"
                )

        else:
            return False, f"Mission {index}: unsupported task"

    return (
        True,
        "All UAV-to-task-to-location associations verified"
    )

if __name__ == "__main__":

    example = (
        "Drone 1 inspect Zone A, "
        "and Drone 2 inspect Zone B."
    )

    correct = {
        "missions": [
            {
                "uav_id": "1",
                "task": "inspect_zone",
                "location": "A"
            },
            {
                "uav_id": "2",
                "task": "inspect_zone",
                "location": "B"
            }
        ]
    }

    swapped = {
        "missions": [
            {
                "uav_id": "1",
                "task": "inspect_zone",
                "location": "B"
            },
            {
                "uav_id": "2",
                "task": "inspect_zone",
                "location": "A"
            }
        ]
    }

    print("Correct:", check_command_grounding(example, correct))
    print("Swapped:", check_command_grounding(example, swapped))
