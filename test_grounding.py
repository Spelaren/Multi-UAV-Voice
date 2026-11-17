
import unittest

from validation.grounding import check_command_grounding


class TestGrounding(unittest.TestCase):

    def test_valid_multi_uav(self):
        command = (
            "Drone 1 inspect Zone A. "
            "Drone 2 inspect Zone B."
        )

        missions = {
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

        valid, _ = check_command_grounding(command, missions)
        self.assertTrue(valid)

    def test_conflicting_zones(self):
        command = "Drone 1 inspect Zone A or Zone B."

        missions = {
            "missions": [
                {
                    "uav_id": "1",
                    "task": "inspect_zone",
                    "location": "A"
                }
            ]
        }

        valid, _ = check_command_grounding(command, missions)
        self.assertFalse(valid)

    def test_question_without_question_mark(self):
        command = "Drone 1 can you inspect Zone A"

        missions = {
            "missions": [
                {
                    "uav_id": "1",
                    "task": "inspect_zone",
                    "location": "A"
                }
            ]
        }

        valid, _ = check_command_grounding(command, missions)
        self.assertFalse(valid)

    def test_repeated_uav_conflicting_zones(self):
        command = (
            "Drone 1 inspect Zone A. "
            "Drone 1 inspect Zone B."
        )

        missions = {
            "missions": [
                {
                    "uav_id": "1",
                    "task": "inspect_zone",
                    "location": "A"
                }
            ]
        }

        valid, _ = check_command_grounding(command, missions)
        self.assertFalse(valid)


    def test_negated_commands(self):
        commands = [
            "Drone 1 should not inspect Zone A.",
            "Drone 1 avoid inspect Zone A.",
            "Drone 1 do not inspect Zone A."
        ]

        missions = {
            "missions": [
                {
                    "uav_id": "1",
                    "task": "inspect_zone",
                    "location": "A"
                }
            ]
        }

        for command in commands:
            with self.subTest(command=command):
                valid, _ = check_command_grounding(
                    command,
                    missions
                )
                self.assertFalse(valid)


    def test_valid_clarification(self):
        command = (
            "Drone 1. "
            "Clarification from user: Drone 1 inspect Zone B."
        )

        missions = {
            "missions": [
                {
                    "uav_id": "1",
                    "task": "inspect_zone",
                    "location": "B"
                }
            ]
        }

        valid, _ = check_command_grounding(command, missions)

        self.assertTrue(valid)


    def test_conflicting_clarification(self):
        command = (
            "Drone 1 inspect Zone A. "
            "Clarification from user: Drone 1 inspect Zone B."
        )

        missions = {
            "missions": [
                {
                    "uav_id": "1",
                    "task": "inspect_zone",
                    "location": "B"
                }
            ]
        }

        valid, _ = check_command_grounding(
            command,
            missions
        )

        self.assertFalse(valid)




    def test_missing_uav_mission(self):
        command = (
            "Drone 1 inspect Zone A. "
            "Drone 2 inspect Zone B."
        )

        missions = {
            "missions": [
                {
                    "uav_id": "1",
                    "task": "inspect_zone",
                    "location": "A"
                }
            ]
        }

        valid, _ = check_command_grounding(
            command,
            missions
        )

        self.assertFalse(valid)


    def test_swapped_uav_destinations(self):
        command = (
            "Drone 1 inspect Zone A. "
            "Drone 2 inspect Zone B."
        )

        missions = {
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

        valid, _ = check_command_grounding(
            command,
            missions
        )

        self.assertFalse(valid)



    def test_wrong_uav_assignment(self):
        command = "Drone 1 inspect Zone A."

        missions = {
            "missions": [
                {
                    "uav_id": "2",
                    "task": "inspect_zone",
                    "location": "A"
                }
            ]
        }

        valid, _ = check_command_grounding(
            command,
            missions
        )

        self.assertFalse(valid)


    def test_missing_inspect_task(self):
        command = "Drone 1, Zone A."

        missions = {
            "missions": [
                {
                    "uav_id": "1",
                    "task": "inspect_zone",
                    "location": "A"
                }
            ]
        }

        valid, _ = check_command_grounding(
            command,
            missions
        )

        self.assertFalse(valid)


    def test_valid_mixed_zone_and_pallet_grounding(self):
        command = (
            "Drone 1 inspect Zone A. "
            "Drone 3 inspect pallet P05."
        )

        missions = {
            "missions": [
                {
                    "uav_id": "1",
                    "task": "inspect_zone",
                    "location": "A"
                },
                {
                    "uav_id": "3",
                    "task": "inspect_pallet",
                    "location": "P05"
                }
            ]
        }

        valid, message = check_command_grounding(
            command,
            missions
        )

        self.assertTrue(valid, message)


    def test_wrong_pallet_assignment(self):
        command = "Drone 3 inspect pallet P05."

        missions = {
            "missions": [
                {
                    "uav_id": "3",
                    "task": "inspect_pallet",
                    "location": "P06"
                }
            ]
        }

        valid, message = check_command_grounding(
            command,
            missions
        )

        self.assertFalse(valid, message)


    def test_conflicting_pallet_locations(self):
        command = "Drone 3 inspect pallet P05 or pallet P06."

        missions = {
            "missions": [
                {
                    "uav_id": "3",
                    "task": "inspect_pallet",
                    "location": "P05"
                }
            ]
        }

        valid, message = check_command_grounding(
            command,
            missions
        )

        self.assertFalse(valid, message)


    def test_pallet_misinterpreted_as_zone(self):
        command = "Drone 3 inspect pallet P05."

        missions = {
            "missions": [
                {
                    "uav_id": "3",
                    "task": "inspect_zone",
                    "location": "A"
                }
            ]
        }

        valid, message = check_command_grounding(
            command,
            missions
        )

        self.assertFalse(valid, message)


    def test_zone_misinterpreted_as_pallet(self):
        command = "Drone 3 inspect Zone A."

        missions = {
            "missions": [
                {
                    "uav_id": "3",
                    "task": "inspect_pallet",
                    "location": "P05"
                }
            ]
        }

        valid, message = check_command_grounding(
            command,
            missions
        )

        self.assertFalse(valid, message)


    def test_swapped_pallet_destinations(self):
        command = (
            "Drone 3 inspect pallet P05. "
            "Drone 4 inspect pallet P06."
        )

        missions = {
            "missions": [
                {
                    "uav_id": "3",
                    "task": "inspect_pallet",
                    "location": "P06"
                },
                {
                    "uav_id": "4",
                    "task": "inspect_pallet",
                    "location": "P05"
                }
            ]
        }

        valid, message = check_command_grounding(
            command,
            missions
        )

        self.assertFalse(valid, message)


    def test_explicit_cancellation_after_command(self):
        transcription = (
            "Drone 3 inspect pallet P05. "
            "Cancel that command."
        )

        mission_data = {
            "missions": [
                {
                    "uav_id": "3",
                    "task": "inspect_pallet",
                    "location": "P05"
                }
            ]
        }

        grounded, message = check_command_grounding(
            transcription,
            mission_data
        )

        self.assertFalse(grounded)
        self.assertEqual(
            message,
            "Negated or cancelled command"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
