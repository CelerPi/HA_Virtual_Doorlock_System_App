import struct
import sys
import unittest
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1] / "addons" / "yunhai_intercom" / "app"
sys.path.insert(0, str(APP_DIR))

from yunhai_intercom.config import load_addon_options
from yunhai_intercom.protocol import (
    MonitorFrameAssembler,
    build_b700_payload,
    build_call_audio_payload,
    build_cd_payload,
    build_identity_payload,
    build_monitor_discovery_payload,
    build_monitor_keepalive_payload,
    build_monitor_request_payload,
    build_monitor_start_payload,
    build_session_info_payload,
    build_session_header,
    build_unlock_payload,
    monitor_broadcast_ip,
    parse_call_audio_packet,
)


class ProtocolPayloadTest(unittest.TestCase):
    def setUp(self):
        self.config = load_addon_options("/tmp/yunhai-missing-options.json")
        self.device_2f = self.config.devices[1]

    def test_unlock_payload_matches_known_2f_packet(self):
        payload = build_unlock_payload(
            self.device_2f,
            self.config.local_ip,
            self.config.local_id,
        )

        self.assertEqual(80, len(payload))
        self.assertEqual(
            (
                "50454e4755494e30"
                "b7000600"
                "00005000"
                "00000000000000000000000000000000"
                "4d3030303130313032303030"
                "0000000000000000"
                "c0a810e1"
                "533030303130313136303130"
                "0000000000000000"
                "c0a81040"
            ),
            payload.hex(),
        )

    def test_monitor_discovery_request_and_keepalive_payloads_match_known_shape(self):
        discovery = build_monitor_discovery_payload(self.device_2f)
        request = build_monitor_request_payload(self.device_2f, self.config.local_ip, self.config.local_id)
        start = build_monitor_start_payload(self.device_2f, self.config.local_ip, self.config.local_id)
        keepalive = build_monitor_keepalive_payload(self.device_2f, self.config.local_ip, self.config.local_id)

        self.assertEqual(35, len(discovery))
        self.assertTrue(discovery.startswith(b"\x01M00010102000"))
        self.assertEqual("192.168.23.255", monitor_broadcast_ip(self.config.local_ip))

        self.assertEqual(172, len(request))
        self.assertEqual(80, request.index(b"VIDEOA"))
        self.assertTrue(request.startswith(bytes.fromhex("50454e4755494e30b80001000000ac00")))
        self.assertIn(b"S00010116010", request)
        self.assertIn(b"M00010102000", request)

        self.assertEqual(80, len(start))
        self.assertTrue(start.startswith(bytes.fromhex("50454e4755494e30b800010000005000")))
        self.assertEqual(80, len(keepalive))
        self.assertTrue(keepalive.startswith(bytes.fromhex("50454e4755494e30b8000c0000005000")))

    def test_proven_b700_call_session_payloads_match_legacy_shape(self):
        identity = build_identity_payload(self.config.local_id)
        cd = build_cd_payload()
        info = build_session_info_payload(self.config.local_ip, self.config.local_id)
        video = build_b700_payload("b7000300", 96, self.device_2f, self.config.local_ip, self.config.local_id)
        keepalive = build_b700_payload("b7000c00", 80, self.device_2f, self.config.local_ip, self.config.local_id)
        unlock = build_unlock_payload(self.device_2f, self.config.local_ip, self.config.local_id)

        self.assertEqual(35, len(identity))
        self.assertTrue(identity.startswith(b"\x02S00010116010"))
        self.assertEqual(bytes.fromhex("50454e4755494e30cd0002000000200000000000000000000000000000000000"), cd)
        self.assertEqual(898, len(info))
        self.assertTrue(info.startswith(bytes.fromhex("50454e4755494e309800020000008203")))
        self.assertIn(b"S00010116010", info)
        self.assertIn(bytes.fromhex("c0a81040"), info)

        self.assertEqual(96, len(video))
        self.assertTrue(video.startswith(bytes.fromhex("50454e4755494e30b700030000006000")))
        self.assertIn(b"M00010102000", video)
        self.assertLess(video.index(b"M00010102000"), video.index(b"S00010116010"))
        self.assertTrue(video.endswith(b"VIDEOA\x00\x002\x00\x09\x00\x09\x00\xff\x00"))

        self.assertEqual(80, len(keepalive))
        self.assertTrue(keepalive.startswith(bytes.fromhex("50454e4755494e30b7000c0000005000")))
        self.assertEqual("b7000600", unlock[8:12].hex())

    def test_monitor_and_call_video_fragments_reassemble_jpeg_frames(self):
        monitor_jpeg = b"\xff\xd8\xff\xe0monitor-jpeg\xff\xd9"
        call_jpeg = b"\xff\xd8\xff\xe0call-jpeg\xff\xd9"
        assembler = MonitorFrameAssembler()

        first_monitor = self._video_packet("b8000a00", 7, 2, 1, monitor_jpeg[:8])
        second_monitor = self._video_packet("b8000a00", 7, 2, 2, monitor_jpeg[8:])
        first_call = self._video_packet("b7000a00", 11, 2, 1, call_jpeg[:9])
        second_call = self._video_packet("b7000a00", 11, 2, 2, call_jpeg[9:])

        self.assertIsNone(assembler.add_packet(first_monitor))
        self.assertEqual(monitor_jpeg, assembler.add_packet(second_monitor))
        self.assertIsNone(assembler.add_packet(first_call))
        self.assertEqual(call_jpeg, assembler.add_packet(second_call))

    def test_audio_channel_media_packets_do_not_become_jpeg_frames(self):
        assembler = MonitorFrameAssembler()
        pcm = b"\x01\x00" * 256
        payload = (
            build_b700_payload(
                "b7000a00",
                90 + len(pcm),
                self.device_2f,
                self.config.local_ip,
                self.config.local_id,
            )
            + struct.pack("<HHHHH", 3, 5, 1, 1, len(pcm))
            + pcm
        )

        self.assertIsNone(assembler.add_packet(payload))

    def test_call_audio_parser_and_builder_use_pcm_channel_three(self):
        pcm = b"\x01\x00" * 256
        payload = build_call_audio_payload(
            self.device_2f,
            self.config.local_ip,
            self.config.local_id,
            sequence=7,
            pcm=pcm,
        )

        self.assertEqual("b7000a00", payload[8:12].hex())
        self.assertEqual(3, struct.unpack_from("<H", payload, 80)[0])
        self.assertEqual(7, struct.unpack_from("<H", payload, 82)[0])
        self.assertEqual(1, struct.unpack_from("<H", payload, 84)[0])
        self.assertEqual(1, struct.unpack_from("<H", payload, 86)[0])
        self.assertEqual(len(pcm), struct.unpack_from("<H", payload, 88)[0])
        self.assertEqual(pcm, parse_call_audio_packet(payload))

    def _video_packet(self, command_hex, frame_no, total_parts, part_no, data):
        if command_hex.startswith("b700"):
            header = build_b700_payload(
                command_hex,
                90 + len(data),
                self.device_2f,
                self.config.local_ip,
                self.config.local_id,
            )
        else:
            header = build_session_header(
                command_hex,
                90 + len(data),
                self.device_2f,
                self.config.local_ip,
                self.config.local_id,
            )
        return (
            header
            + struct.pack("<HHHHH", 1, frame_no, total_parts, part_no, len(data))
            + data
        )


if __name__ == "__main__":
    unittest.main()
