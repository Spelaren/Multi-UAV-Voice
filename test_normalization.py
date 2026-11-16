
import unittest


from Audio.normalization import normalize_pallet_identifiers



class TestPalletNormalization(unittest.TestCase):

    def test_hyphenated_pallet(self):
        result = normalize_pallet_identifiers(
            "Drone 3, inspect pallet P-05"
        )
        self.assertEqual(
            result,
            "Drone 3, inspect pallet P05"
        )

    def test_spaced_pallet(self):
        result = normalize_pallet_identifiers(
            "Drone 3, inspect pallet P 05"
        )
        self.assertEqual(
            result,
            "Drone 3, inspect pallet P05"
        )

    def test_already_normalized(self):
        result = normalize_pallet_identifiers(
            "Drone 3, inspect pallet P05"
        )
        self.assertEqual(
            result,
            "Drone 3, inspect pallet P05"
        )

    def test_invalid_pallet_stays_invalid(self):
        result = normalize_pallet_identifiers(
            "Drone 3, inspect pallet P-98"
        )
        self.assertEqual(
            result,
            "Drone 3, inspect pallet P98"
        )

    def test_other_words_unchanged(self):
        result = normalize_pallet_identifiers(
            "Drone 3, inspect Zone A"
        )
        self.assertEqual(
            result,
            "Drone 3, inspect Zone A"
        )

    def test_non_string_input(self):
        self.assertIsNone(
            normalize_pallet_identifiers(None)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
