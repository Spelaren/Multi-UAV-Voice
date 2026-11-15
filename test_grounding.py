
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

if __name__ == "__main__":
    unittest.main(verbosity=2)
