
import unittest

from validation.negation import contains_explicit_negation


class TestNegation(unittest.TestCase):

    def test_do_not_inspect(self):
        text = "Drone 2, do not inspect pallet P05."
        self.assertTrue(contains_explicit_negation(text))

    def test_dont_inspect(self):
        text = "Drone 2, don't inspect Zone A."
        self.assertTrue(contains_explicit_negation(text))

    def test_normal_inspection(self):
        text = "Drone 2, inspect pallet P05."
        self.assertFalse(contains_explicit_negation(text))

    def test_empty_input(self):
        self.assertFalse(contains_explicit_negation(""))

    def test_non_string_input(self):
        self.assertFalse(contains_explicit_negation(None))


if __name__ == "__main__":
    unittest.main(verbosity=2)
