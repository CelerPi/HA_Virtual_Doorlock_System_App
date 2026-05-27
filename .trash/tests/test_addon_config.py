import json
import sys
import tempfile
import unittest
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1] / "addons" / "uppercoast_doorlock" / "app"
sys.path.insert(0, str(APP_DIR))

from uppercoast_doorlock.config import load_addon_options


class AddonConfigTest(unittest.TestCase):
    def test_missing_options_file_uses_1a_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            options_path = Path(temp_dir) / "options.json"

            config = load_addon_options(options_path)

        self.assertEqual("192.168.16.64", config.local_ip)
        self.assertEqual("00010116010", config.local_id)
        self.assertEqual("building_1_a", config.building_id)
        self.assertEqual("1栋A座", config.building_name)
        self.assertEqual("192.168.16.2", config.center_ip)
        self.assertEqual("192.168.16.3", config.property_center_ip)
        self.assertEqual(8, len(config.devices))

        devices_by_door = {device.door_no: device for device in config.devices}
        self.assertEqual("1号机", devices_by_door["01"].display_name)
        self.assertEqual("192.168.16.224", devices_by_door["01"].target_ip)
        self.assertEqual("1层", devices_by_door["01"].floor_label)
        self.assertEqual("车库", devices_by_door["01"].position_detail)
        self.assertEqual("192.168.16.225", devices_by_door["02"].target_ip)
        self.assertEqual("2层", devices_by_door["02"].floor_label)
        self.assertEqual("花园", devices_by_door["02"].position_detail)
        self.assertEqual("192.168.23.165", devices_by_door["08"].target_ip)
        self.assertEqual("电梯正对", devices_by_door["08"].position_detail)

    def test_building_2c_keeps_station_layout_and_known_ips(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            options_path = Path(temp_dir) / "options.json"
            options_path.write_text(
                json.dumps(
                    {
                        "local_ip": "192.168.16.88",
                        "local_id": "00010122010",
                        "building_id": "building_2_c",
                    }
                ),
                encoding="utf-8",
            )

            config = load_addon_options(options_path)

        self.assertEqual("192.168.16.88", config.local_ip)
        self.assertEqual("00010122010", config.local_id)
        self.assertEqual("building_2_c", config.building_id)
        self.assertEqual("2栋C座", config.building_name)
        self.assertEqual(7, len(config.devices))
        self.assertEqual(7, len(config.active_devices))
        self.assertEqual("192.168.23.155", config.devices[0].target_ip)
        self.assertEqual("1层", config.devices[0].floor_label)
        self.assertEqual("192.168.23.160", config.devices[4].target_ip)
        self.assertEqual("-2层", config.devices[5].floor_label)

    def test_chinese_building_option_loads_matching_building_rules(self):
        config = load_addon_options(
            _write_temp_options(
                {
                    "building_id": "2栋C座",
                    "local_ip": "192.168.23.64",
                    "local_id": "00010123010",
                }
            )
        )

        devices = {device.door_no: device for device in config.devices}
        self.assertEqual("building_2_c", config.building_id)
        self.assertEqual("2栋C座", config.building_name)
        self.assertEqual("192.168.23.155", devices["01"].target_ip)
        self.assertEqual("192.168.23.169", devices["08"].target_ip)

    def test_unknown_building_falls_back_to_default_preset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            options_path = Path(temp_dir) / "options.json"
            options_path.write_text(
                json.dumps({"building_id": "building_9_z"}),
                encoding="utf-8",
            )

            config = load_addon_options(options_path)

        self.assertEqual("building_1_a", config.building_id)
        self.assertEqual("1栋A座", config.building_name)
        self.assertEqual(8, len(config.devices))
        self.assertEqual(8, len(config.active_devices))

    def test_building_1b_uses_rule_table_with_exceptions(self):
        config = load_addon_options(
            _write_temp_options(
                {
                    "building_id": "building_1_b",
                    "local_ip": "192.168.18.64",
                    "local_id": "00010118010",
                }
            )
        )

        devices = {device.door_no: device for device in config.devices}
        self.assertEqual("192.168.18.96", devices["01"].target_ip)
        self.assertEqual("192.168.18.97", devices["02"].target_ip)
        self.assertEqual("192.168.18.98", devices["03"].target_ip)
        self.assertEqual("192.168.18.99", devices["04"].target_ip)
        self.assertEqual("192.168.18.100", devices["05"].target_ip)
        self.assertEqual("192.168.18.101", devices["06"].target_ip)
        self.assertEqual("192.168.23.167", devices["07"].target_ip)
        self.assertEqual(7, len(config.devices))

    def test_building_1c_uses_rule_table(self):
        config = load_addon_options(
            _write_temp_options(
                {
                    "building_id": "building_1_c",
                    "local_ip": "192.168.19.64",
                    "local_id": "00010119010",
                }
            )
        )

        devices = {device.door_no: device for device in config.devices}
        self.assertEqual("192.168.19.98", devices["01"].target_ip)
        self.assertEqual("192.168.19.99", devices["02"].target_ip)
        self.assertEqual("192.168.19.100", devices["03"].target_ip)
        self.assertEqual("192.168.19.101", devices["04"].target_ip)
        self.assertEqual("192.168.19.102", devices["05"].target_ip)
        self.assertEqual("192.168.19.103", devices["06"].target_ip)
        self.assertEqual("192.168.23.168", devices["07"].target_ip)
        self.assertEqual(7, len(config.devices))

    def test_building_1d_uses_rule_table_and_leaves_missing_devices_blank(self):
        config = load_addon_options(
            _write_temp_options(
                {
                    "building_id": "building_1_d",
                    "local_ip": "192.168.19.64",
                    "local_id": "00010119010",
                }
            )
        )

        devices = {device.door_no: device for device in config.devices}
        self.assertEqual("192.168.19.219", devices["01"].target_ip)
        self.assertEqual("192.168.19.220", devices["02"].target_ip)
        self.assertEqual("192.168.19.221", devices["03"].target_ip)
        self.assertEqual("192.168.19.222", devices["04"].target_ip)
        self.assertEqual("192.168.19.223", devices["05"].target_ip)
        self.assertEqual("192.168.19.224", devices["06"].target_ip)
        self.assertEqual("192.168.23.163", devices["07"].target_ip)
        self.assertEqual("192.168.23.164", devices["08"].target_ip)
        self.assertEqual(8, len(config.devices))

    def test_building_2c_uses_rule_table_with_missing_slot(self):
        config = load_addon_options(
            _write_temp_options(
                {
                    "building_id": "building_2_c",
                    "local_ip": "192.168.23.64",
                    "local_id": "00010123010",
                }
            )
        )

        devices = {device.door_no: device for device in config.devices}
        self.assertEqual("192.168.23.155", devices["01"].target_ip)
        self.assertEqual("192.168.23.156", devices["02"].target_ip)
        self.assertEqual("192.168.23.157", devices["03"].target_ip)
        self.assertEqual("192.168.23.158", devices["04"].target_ip)
        self.assertEqual("192.168.23.160", devices["06"].target_ip)
        self.assertEqual("192.168.23.161", devices["07"].target_ip)
        self.assertEqual("192.168.23.169", devices["08"].target_ip)
        self.assertEqual(7, len(config.devices))

    def test_door_ip_options_override_building_defaults(self):
        config = load_addon_options(
            _write_temp_options(
                {
                    "building_id": "building_1_a",
                    "door_02_ip": "192.168.16.250",
                    "door_03_ip": "",
                }
            )
        )

        devices = {device.door_no: device for device in config.devices}
        self.assertEqual("192.168.16.250", devices["02"].target_ip)
        self.assertEqual("192.168.16.226", devices["03"].target_ip)

    def test_door_ip_options_do_not_create_missing_building_devices(self):
        config = load_addon_options(
            _write_temp_options(
                {
                    "building_id": "building_2_b",
                    "door_08_ip": "192.168.22.188",
                }
            )
        )

        devices = {device.door_no: device for device in config.devices}
        self.assertNotIn("08", devices)
        self.assertEqual(4, len(config.devices))

    def test_all_building_ip_rules_match_collected_export(self):
        expected_by_building = {
            "building_1_a": {
                "01": "192.168.16.224",
                "02": "192.168.16.225",
                "03": "192.168.16.226",
                "04": "192.168.16.227",
                "05": "192.168.16.228",
                "06": "192.168.16.229",
                "07": "192.168.23.164",
                "08": "192.168.23.165",
            },
            "building_1_b": {
                "01": "192.168.18.96",
                "02": "192.168.18.97",
                "03": "192.168.18.98",
                "04": "192.168.18.99",
                "05": "192.168.18.100",
                "06": "192.168.18.101",
                "07": "192.168.23.167",
            },
            "building_1_c": {
                "01": "192.168.19.98",
                "02": "192.168.19.99",
                "03": "192.168.19.100",
                "04": "192.168.19.101",
                "05": "192.168.19.102",
                "06": "192.168.19.103",
                "07": "192.168.23.168",
            },
            "building_1_d": {
                "01": "192.168.19.219",
                "02": "192.168.19.220",
                "03": "192.168.19.221",
                "04": "192.168.19.222",
                "05": "192.168.19.223",
                "06": "192.168.19.224",
                "07": "192.168.23.163",
                "08": "192.168.23.164",
            },
            "building_1_e": {
                "01": "192.168.20.116",
                "02": "192.168.20.117",
                "03": "192.168.20.118",
                "04": "192.168.20.119",
                "05": "192.168.20.120",
            },
            "building_2_a": {
                "01": "192.168.21.212",
                "02": "192.168.21.213",
                "03": "192.168.21.214",
                "04": "192.168.21.215",
                "05": "192.168.21.216",
                "06": "192.168.21.217",
            },
            "building_2_b": {
                "01": "192.168.22.184",
                "02": "192.168.22.185",
                "03": "192.168.22.186",
                "04": "192.168.22.187",
            },
            "building_2_c": {
                "01": "192.168.23.155",
                "02": "192.168.23.156",
                "03": "192.168.23.157",
                "04": "192.168.23.158",
                "06": "192.168.23.160",
                "07": "192.168.23.161",
                "08": "192.168.23.169",
            },
        }

        for building_id, expected_ips in expected_by_building.items():
            with self.subTest(building_id=building_id):
                config = load_addon_options(_write_temp_options({"building_id": building_id}))
                actual_ips = {device.door_no: device.target_ip for device in config.devices}
                self.assertEqual(expected_ips, actual_ips)


def _write_temp_options(data):
    temp_dir = tempfile.mkdtemp()
    options_path = Path(temp_dir) / "options.json"
    options_path.write_text(json.dumps(data), encoding="utf-8")
    return options_path


if __name__ == "__main__":
    unittest.main()
