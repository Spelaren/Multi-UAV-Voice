
import unittest
from unittest.mock import Mock

from app import SLMApp


class TestSendMission(unittest.TestCase):

    def setUp(self):
        # Test the method without starting Tkinter.
        self.app = SLMApp.__new__(SLMApp)

        self.app.recording = False
        self.app.processing = False
        self.app.cancelled = False

        self.app.validated_mission = {
            "missions": [
                {
                    "uav_id": "2",
                    "task": "inspect_zone",
                    "location": "A"
                }
            ]
        }

        self.app.send_button = Mock()
        self.app.status_label = Mock()
        self.app.log = Mock()

    def test_confirmation_without_valid_mission(self):
        self.app.validated_mission = None

        self.app.send_mission()

        self.app.send_button.configure.assert_called_with(
            state="disabled"
        )
        self.app.log.assert_called_with(
            "Mission confirmation blocked - no valid mission"
        )

    def test_confirmation_blocked_during_processing(self):
        self.app.processing = True

        self.app.send_mission()

        self.app.log.assert_called_with(
            "Mission confirmation blocked - system busy"
        )
        self.assertIsNotNone(self.app.validated_mission)

    def test_confirmation_blocked_after_cancellation(self):
        self.app.cancelled = True

        self.app.send_mission()

        self.app.send_button.configure.assert_called_with(
            state="disabled"
        )
        self.app.log.assert_called_with(
            "Mission confirmation blocked - no valid mission"
        )

    def test_valid_mission_confirmed_once(self):
        self.app.send_mission()

        self.assertIsNone(self.app.validated_mission)

        self.app.log.assert_any_call(
            "Validated mission confirmed by user"
        )
        self.app.log.assert_any_call(
            "No UAV command dispatched - dispatch adapter not integrated"
        )

        # A second confirmation must be rejected.
        self.app.log.reset_mock()

        self.app.send_mission()

        self.app.log.assert_called_with(
            "Mission confirmation blocked - no valid mission"
        )


if __name__ == "__main__":
    unittest.main()
