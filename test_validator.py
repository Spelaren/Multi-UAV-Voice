
import json
import unittest

from validation.validator import validate_missions


class TestWarehouseValidator(unittest.TestCase):

    def test_valid_zone_mission(self):
        data = {
            "missions": [
                {
                    "uav_id": "1",
                    "task": "inspect_zone",
                    "location": "A"
                }
            ]
        }

        valid, _ = validate_missions(json.dumps(data))

        self.assertTrue(valid)

    def test_invalid_uav_id(self):
        data = {
            "missions": [
                {
                    "uav_id": "99",
                    "task": "inspect_zone",
                    "location": "A"
                }
            ]
        }

        valid, _ = validate_missions(json.dumps(data))

        self.assertFalse(valid)

    def test_duplicate_uav_assignment(self):
        data = {
            "missions": [
                {
                    "uav_id": "1",
                    "task": "inspect_zone",
                    "location": "A"
                },
                {
                    "uav_id": "1",
                    "task": "inspect_zone",
                    "location": "B"
                }
            ]
        }

        valid, _ = validate_missions(json.dumps(data))

        self.assertFalse(valid)


    def test_invalid_zone(self):
        data = {
            "missions": [
                {
                    "uav_id": "1",
                    "task": "inspect_zone",
                    "location": "INVALID_ZONE"
                }
            ]
        }

        valid, message = validate_missions(
            json.dumps(data)
        )

        self.assertFalse(valid)
        self.assertIn("invalid zone", message)


    def test_invalid_pallet_location(self):
        data = {
            "missions": [
                {
                    "uav_id": "1",
                    "task": "inspect_pallet",
                    "location": "INVALID_PALLET"
                }
            ]
        }

        valid, message = validate_missions(
            json.dumps(data)
        )

        self.assertFalse(valid)
        self.assertIn("invalid pallet", message)


    def test_invalid_task(self):
        data = {
            "missions": [
                {
                    "uav_id": "1",
                    "task": "deliver_package",
                    "location": "A"
                }
            ]
        }

        valid, message = validate_missions(
            json.dumps(data)
        )

        self.assertFalse(valid)
        self.assertIn("task not allowed", message)


    def test_invalid_json(self):
        model_output = '{"missions": ['

        valid, message = validate_missions(model_output)

        self.assertFalse(valid)
        self.assertEqual(message, "Invalid JSON format")


    def test_wrong_json_structure(self):
        data = {
            "tasks": []
        }

        valid, message = validate_missions(
            json.dumps(data)
        )

        self.assertFalse(valid)
        self.assertEqual(
            message,
            "JSON must contain exactly the 'missions' field"
        )


    def test_empty_missions_list(self):
        data = {
            "missions": []
        }

        valid, message = validate_missions(
            json.dumps(data)
        )

        self.assertFalse(valid)
        self.assertEqual(
            message,
            "Missions must be a non-empty list"
        )



    def test_missing_mission_field(self):
        data = {
            "missions": [
                {
                    "uav_id": "1",
                    "task": "inspect_zone"
                }
            ]
        }

        valid, message = validate_missions(
            json.dumps(data)
        )

        self.assertFalse(valid)
        self.assertEqual(
            message,
            "Mission 1: incorrect fields"
        )


    def test_null_uav_id(self):
        data = {
            "missions": [
                {
                    "uav_id": None,
                    "task": "inspect_zone",
                    "location": "A"
                }
            ]
        }

        valid, message = validate_missions(
            json.dumps(data)
        )

        self.assertFalse(valid)
        self.assertEqual(
            message,
            "Mission 1: fields must be strings"
        )



    def test_valid_pallet_mission(self):
        data = {
            "missions": [
                {
                    "uav_id": "3",
                    "task": "inspect_pallet",
                    "location": "P05"
                }
            ]
        }

        valid, result = validate_missions(
            json.dumps(data)
        )

        self.assertTrue(valid)
        self.assertEqual(result, data)


    def test_valid_mixed_multi_uav_missions(self):
        data = {
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

        valid, result = validate_missions(
            json.dumps(data)
        )

        self.assertTrue(valid)
        self.assertEqual(result, data)



if __name__ == "__main__":
    unittest.main(verbosity=2)
