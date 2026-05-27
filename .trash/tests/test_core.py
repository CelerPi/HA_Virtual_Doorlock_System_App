import struct
import sys
import unittest
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1] / "addons" / "uppercoast_doorlock" / "app"
sys.path.insert(0, str(APP_DIR))

from uppercoast_doorlock.config import load_addon_options
from uppercoast_doorlock.core import (
    CALL_AUDIO_CHANNEL,
    CALL_AUDIO_SAMPLES_PER_PACKET,
    CALL_UNLOCK_REPEAT,
    IntercomCore,
)


class FakeSocket:
    def __init__(self):
        self.sent_packets = []

    def sendto(self, payload, address):
        self.sent_packets.append((payload, address))


class CoreActionTest(unittest.TestCase):
    def setUp(self):
        self.config = load_addon_options("/tmp/uppercoast-missing-options.json")
        self.device = self.config.devices[1]
        self.core = IntercomCore(self.config)
        self.core.frame_hub.begin_call(self.device)

    def test_unlock_request_sends_b7000600_burst_for_current_call(self):
        state = {"active": True, "device": self.device, "expires_at": 0}
        fake_socket = FakeSocket()

        self.assertTrue(self.core.request_unlock(self.device.target_ip))
        for _ in range(CALL_UNLOCK_REPEAT):
            state["next_unlock_at"] = 0
            state = self.core.run_unlock_timers(state, fake_socket)

        self.assertEqual(CALL_UNLOCK_REPEAT, len(fake_socket.sent_packets))
        payload, address = fake_socket.sent_packets[0]
        self.assertEqual((self.device.target_ip, 10000), address)
        self.assertEqual("b7000600", payload[8:12].hex())
        self.assertIn(b"M00010102000", payload)
        self.assertEqual(0, state["unlock_remaining"])

    def test_answer_request_sends_b7000500_for_current_call(self):
        state = {"active": True, "device": self.device, "expires_at": 0}
        fake_socket = FakeSocket()

        self.assertTrue(self.core.request_answer(self.device.target_ip))
        state = self.core.run_answer_timers(state, fake_socket)

        payload, address = fake_socket.sent_packets[-1]
        self.assertEqual((self.device.target_ip, 10000), address)
        self.assertEqual("b7000500", payload[8:12].hex())

    def test_microphone_audio_is_chunked_and_sent_as_channel_three(self):
        state = {"active": True, "device": self.device, "expires_at": 0, "audio_sequence": 0}
        fake_socket = FakeSocket()
        pcm = b"\x01\x00" * CALL_AUDIO_SAMPLES_PER_PACKET

        self.assertTrue(self.core.request_outgoing_audio(self.device.target_ip, pcm))
        state = self.core.run_outgoing_audio_timers(state, fake_socket)

        payload, address = fake_socket.sent_packets[-1]
        self.assertEqual((self.device.target_ip, 10000), address)
        self.assertEqual("b7000a00", payload[8:12].hex())
        self.assertEqual(CALL_AUDIO_CHANNEL, struct.unpack_from("<H", payload, 80)[0])
        self.assertEqual(1, struct.unpack_from("<H", payload, 82)[0])
        self.assertEqual(len(pcm), struct.unpack_from("<H", payload, 88)[0])
        self.assertEqual(pcm, payload[90:])

    def test_actions_are_rejected_without_matching_current_call(self):
        core = IntercomCore(self.config)

        self.assertFalse(core.request_unlock(self.device.target_ip))
        self.assertFalse(core.request_answer(self.device.target_ip))
        self.assertFalse(core.request_outgoing_audio(self.device.target_ip, b"\x00\x00"))


if __name__ == "__main__":
    unittest.main()
