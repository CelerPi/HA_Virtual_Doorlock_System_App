import json
import sys
import tempfile
import unittest
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1] / "addons" / "yunhai_intercom" / "app"
sys.path.insert(0, str(APP_DIR))

from yunhai_intercom.config import normalize_options
from yunhai_intercom.store import ConfigStore


class ConfigStoreTest(unittest.TestCase):
    def test_missing_store_is_seeded_from_addon_options(self):
        defaults = normalize_options({"local_ip": "192.168.16.88", "building_id": "building_1_a"})

        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "yunhai_config.json"
            config = ConfigStore(store_path).load(defaults)
            saved = json.loads(store_path.read_text(encoding="utf-8"))

        self.assertEqual("192.168.16.88", config.local_ip)
        self.assertEqual("building_1_a", config.building_id)
        self.assertEqual(8, len(config.active_devices))
        self.assertEqual("192.168.16.225", saved["devices"][1]["target_ip"])

    def test_store_preserves_device_ip_overrides_while_options_control_identity(self):
        defaults = normalize_options(
            {
                "local_ip": "192.168.16.99",
                "local_id": "00010199010",
                "building_id": "building_1_a",
            }
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "yunhai_config.json"
            store_path.write_text(
                json.dumps(
                    {
                        "local_ip": "192.168.16.64",
                        "local_id": "00010116010",
                        "building_id": "building_1_a",
                        "devices": [
                            {"name": "2F-2", "door_no": "02", "target_ip": "192.168.16.250"},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            config = ConfigStore(store_path).load(defaults)

        devices_by_door = {device.door_no: device for device in config.devices}
        self.assertEqual("192.168.16.99", config.local_ip)
        self.assertEqual("00010199010", config.local_id)
        self.assertEqual("192.168.16.250", devices_by_door["02"].target_ip)

    def test_switching_building_discards_previous_building_device_overrides(self):
        defaults = normalize_options({"building_id": "building_2_c"})

        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "yunhai_config.json"
            store_path.write_text(
                json.dumps(
                    {
                        "building_id": "building_1_a",
                        "devices": [
                            {"name": "2F-2", "door_no": "02", "target_ip": "192.168.16.250"},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            config = ConfigStore(store_path).load(defaults)

        self.assertEqual("building_2_c", config.building_id)
        self.assertEqual([], config.active_devices)


if __name__ == "__main__":
    unittest.main()
