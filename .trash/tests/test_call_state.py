import sys
import unittest
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1] / "addons" / "uppercoast_doorlock" / "app"
sys.path.insert(0, str(APP_DIR))

from uppercoast_doorlock.call_state import CallStateTracker, devices_by_ip, parse_penguin_command
from uppercoast_doorlock.config import load_addon_options, normalize_options


class CallStateTest(unittest.TestCase):
    def test_devices_by_ip_uses_only_active_configured_stations(self):
        default_config = load_addon_options("/tmp/uppercoast-missing-options.json")
        blank_config = normalize_options({"building_id": "building_2_c"})

        active = devices_by_ip(default_config)

        self.assertEqual(8, len(active))
        self.assertEqual("1F-1", active["192.168.16.224"].name)
        self.assertEqual("B1-3", active["192.168.16.226"].name)
        self.assertEqual("1F-8", active["192.168.23.165"].name)
        self.assertEqual(7, len(devices_by_ip(blank_config)))

    def test_penguin_command_parser_extracts_command_or_dash(self):
        payload = bytes.fromhex("50454e4755494e30cd00010000002000")

        self.assertEqual("cd000100", parse_penguin_command(payload))
        self.assertEqual("-", parse_penguin_command(b"not-penguin"))

    def test_call_trigger_from_known_station_begins_current_call(self):
        config = load_addon_options("/tmp/uppercoast-missing-options.json")
        tracker = CallStateTracker(config)
        payload = bytes.fromhex("50454e4755494e30b700010000002000")

        event = tracker.handle_packet(payload, ("192.168.16.226", 10000))
        snapshot = tracker.snapshot()

        self.assertEqual("call_started", event.kind)
        self.assertEqual("b7000100", event.command)
        self.assertEqual("B1-3", event.device.name)
        self.assertTrue(snapshot["in_call"])
        self.assertEqual("192.168.16.226", snapshot["target_ip"])
        self.assertEqual("3号机", snapshot["display_name"])
        self.assertEqual("-1层", snapshot["floor_label"])

    def test_call_end_only_closes_the_current_station_call(self):
        config = load_addon_options("/tmp/uppercoast-missing-options.json")
        tracker = CallStateTracker(config)
        trigger = bytes.fromhex("50454e4755494e30cd00010000002000")
        end = bytes.fromhex("50454e4755494e30b400060000002200000000000000000000000000000000000100")

        tracker.handle_packet(trigger, ("192.168.16.225", 10000))

        self.assertIsNone(tracker.handle_packet(end, ("192.168.16.226", 10000)))
        self.assertTrue(tracker.snapshot()["in_call"])

        event = tracker.handle_packet(end, ("192.168.16.225", 10000))
        snapshot = tracker.snapshot()

        self.assertEqual("call_ended", event.kind)
        self.assertEqual("b4000600", event.command)
        self.assertFalse(snapshot["in_call"])
        self.assertEqual("", snapshot["target_ip"])

    def test_packets_from_unknown_ip_are_ignored(self):
        config = load_addon_options("/tmp/uppercoast-missing-options.json")
        tracker = CallStateTracker(config)
        payload = bytes.fromhex("50454e4755494e30cd00010000002000")

        self.assertIsNone(tracker.handle_packet(payload, ("192.168.99.99", 10000)))
        self.assertFalse(tracker.snapshot()["in_call"])


if __name__ == "__main__":
    unittest.main()
