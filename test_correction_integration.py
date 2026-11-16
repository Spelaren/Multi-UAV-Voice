
import unittest

from validation.correction import validate_location_correction
from validation.grounding import check_command_grounding


class TestCorrectionIntegration(unittest.TestCase):

    def test_corrected_mission_matches_voice_answer(self):
        original = "Drone 3 inspect pallet P99."
        answer = "Drone 3 inspect pallet P05."

        mission_data = {
            "missions": [
                {
                    "uav_id": "3",
                    "task": "inspect_pallet",
                    "location": "P05"
                }
            ]
        }

        correction_valid, message = validate_location_correction(
            original, answer
        )
        self.assertTrue(correction_valid, message)

        grounded, message = check_command_grounding(
            answer, mission_data
        )
        self.assertTrue(grounded, message)

    def test_corrected_mission_wrong_pallet(self):
        original = "Drone 3 inspect pallet P99."
        answer = "Drone 3 inspect pallet P05."

        mission_data = {
            "missions": [
                {
                    "uav_id": "3",
                    "task": "inspect_pallet",
                    "location": "P06"
                }
            ]
        }

        correction_valid, _ = validate_location_correction(
            original, answer
        )
        self.assertTrue(correction_valid)

        grounded, _ = check_command_grounding(
            answer, mission_data
        )
        self.assertFalse(grounded)

    def test_corrected_mission_wrong_uav(self):
        original = "Drone 3 inspect pallet P99."
        answer = "Drone 3 inspect pallet P05."

        mission_data = {
            "missions": [
                {
                    "uav_id": "4",
                    "task": "inspect_pallet",
                    "location": "P05"
                }
            ]
        }

        correction_valid, _ = validate_location_correction(
            original, answer
        )
        self.assertTrue(correction_valid)

        grounded, _ = check_command_grounding(
            answer, mission_data
        )
        self.assertFalse(grounded)


if __name__ == "__main__":
    unittest.main(verbosity=2)
