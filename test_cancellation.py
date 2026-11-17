
import unittest

from validation.cancellation import contains_explicit_cancellation


class TestCancellation(unittest.TestCase):

    def test_cancel_that_command(self):
        text = "Drone 3 inspect pallet P05. Cancel that command."
        self.assertTrue(contains_explicit_cancellation(text))

    def test_cancel_this_mission(self):
        text = "Cancel this mission"
        self.assertTrue(contains_explicit_cancellation(text))

    def test_stop_the_command(self):
        text = "Stop the command"
        self.assertTrue(contains_explicit_cancellation(text))

    def test_never_mind(self):
        text = "Never mind"
        self.assertTrue(contains_explicit_cancellation(text))

    def test_normal_inspection_command(self):
        text = "Drone 3 inspect pallet P05"
        self.assertFalse(contains_explicit_cancellation(text))

    def test_question_without_cancellation(self):
        text = "Can Drone 3 inspect pallet P05?"
        self.assertFalse(contains_explicit_cancellation(text))

    def test_empty_transcription(self):
        self.assertFalse(contains_explicit_cancellation(""))

    def test_non_string_input(self):
        self.assertFalse(contains_explicit_cancellation(None))


if __name__ == "__main__":
    unittest.main(verbosity=2)
