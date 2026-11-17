
import unittest

from validation.correction import validate_location_correction


class TestLocationCorrection(unittest.TestCase):

    def test_valid_pallet_correction(self):
        original = "Drone 3 inspect pallet P99."
        answer = "Drone 3 inspect pallet P05."

        valid, message = validate_location_correction(
            original, answer
        )

        self.assertTrue(valid, message)

    def test_invalid_corrected_pallet(self):
        original = "Drone 3 inspect pallet P99."
        answer = "Drone 3 inspect pallet P98."

        valid, message = validate_location_correction(
            original, answer
        )

        self.assertFalse(valid)

    def test_original_pallet_already_valid(self):
        original = "Drone 3 inspect pallet P05."
        answer = "Drone 3 inspect pallet P06."

        valid, message = validate_location_correction(
            original, answer
        )

        self.assertFalse(valid)

    def test_uav_changed_during_correction(self):
        original = "Drone 3 inspect pallet P99."
        answer = "Drone 4 inspect pallet P05."

        valid, message = validate_location_correction(
            original, answer
        )

        self.assertFalse(valid)

    def test_incomplete_correction_answer(self):
        original = "Drone 3 inspect pallet P99."
        answer = "P05"

        valid, message = validate_location_correction(
            original, answer
        )

        self.assertFalse(valid)



    def test_pallet_correction_with_commas(self):
        original = "Drone 3, Inspect Pallet, P99"
        answer = "Drone 3, Inspect Pallet P05"

        valid, message = validate_location_correction(
            original,
            answer
        )

        self.assertTrue(valid, message)


    def test_uav_change_with_comma_transcription(self):
        original = "Drone 3, Inspect Pallet P99"
        answer = "Drone 4, Inspect Pallet, P05"

        valid, message = validate_location_correction(
            original,
            answer
        )

        self.assertFalse(valid)
        self.assertEqual(
            message,
            "UAV ID cannot change during correction"
        )


    def test_misrecognized_pallet_word(self):
        original = "Drone 3, Inspect Pallet P99"
        answer = "Drone 3, Inspect Palette, P05"

        valid, message = validate_location_correction(
            original,
            answer
        )

        self.assertFalse(valid)
        self.assertEqual(
            message,
            "Correction requires complete pallet commands"
        )


    def test_reject_uav_change_with_period(self):
        original = "Drone 4, Inspect Pallet P99"
        clarification = "Drone 5. Inspect Pallet P05."

        valid, reason = validate_location_correction(
            original,
            clarification
        )

        self.assertFalse(valid)
        self.assertEqual(
            reason,
            "UAV ID cannot change during correction"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
