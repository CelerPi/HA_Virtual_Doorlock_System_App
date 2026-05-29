from __future__ import annotations

import ipaddress
import socket
import struct
from dataclasses import dataclass
from typing import Any


TARGET_PORT = 10000
MONITOR_DISCOVERY_PORT = 10008
PENGUIN_HEADER_HEX = "50454e4755494e30"
PADDING_HEX = "0000000000000000"
MONITOR_VIDEO_DATA_OFFSET = 90
CALL_AUDIO_CHANNEL = 3
VIDEO_FRAGMENT_COMMANDS = {"b7000a00", "b8000a00"}
B700_VIDEO_TAIL_HEX = "564944454f410000320009000900ff00"

MONITOR_VIDEO_TAIL_HEX = (
    "0100320000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000001000900000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000ff00"
)


@dataclass(frozen=True)
class VideoFragment:
    frame_no: int
    total_parts: int
    part_no: int
    data: bytes


def build_unlock_payload(device: Any, local_ip: str, local_id: str) -> bytes:
    return build_b700_payload("b7000600", 80, device, local_ip, local_id)


def build_identity_payload(local_id: str) -> bytes:
    device_id = f"S{local_id}".encode("ascii")
    return b"\x02" + device_id + bytes(35 - 1 - len(device_id))


def build_cd_payload() -> bytes:
    return bytes.fromhex(
        "".join(
            [
                PENGUIN_HEADER_HEX,
                "cd000200",
                "00002000",
                "00000000000000000000000000000000",
            ]
        )
    )


def build_session_info_payload(local_ip: str, local_id: str) -> bytes:
    payload_hex = "".join(
        [
            PENGUIN_HEADER_HEX,
            "98000200",
            "0000",
            _word_to_little_hex(898),
            "00000000000000000000000000000000",
            "0100",
            _text_to_hex(f"S{local_id}"),
            PADDING_HEX,
            _ip_to_hex(local_ip),
        ]
    )
    payload = bytes.fromhex(payload_hex)
    return payload + bytes(898 - len(payload))


def build_b700_payload(
    command_hex: str,
    payload_length: int,
    device: Any,
    local_ip: str,
    local_id: str,
) -> bytes:
    payload_hex = "".join(
        [
            PENGUIN_HEADER_HEX,
            command_hex,
            "0000",
            _word_to_little_hex(payload_length),
            "00000000000000000000000000000000",
            _text_to_hex(f"M000101{_device_value(device, 'door_no')}000"),
            PADDING_HEX,
            _ip_to_hex(_device_value(device, "target_ip")),
            _text_to_hex(f"S{local_id}"),
            PADDING_HEX,
            _ip_to_hex(local_ip),
        ]
    )

    if command_hex == "b7000300":
        payload_hex += B700_VIDEO_TAIL_HEX

    return bytes.fromhex(payload_hex)


def build_call_audio_payload(device: Any, local_ip: str, local_id: str, sequence: int, pcm: bytes) -> bytes:
    if not pcm or len(pcm) % 2 != 0:
        raise ValueError("audio data must be 16-bit PCM")

    sequence &= 0xFFFF
    if sequence == 0:
        sequence = 1

    return (
        build_b700_payload("b7000a00", MONITOR_VIDEO_DATA_OFFSET + len(pcm), device, local_ip, local_id)
        + struct.pack("<HHHHH", CALL_AUDIO_CHANNEL, sequence, 1, 1, len(pcm))
        + pcm
    )


def parse_call_audio_packet(payload: bytes) -> bytes | None:
    if len(payload) < MONITOR_VIDEO_DATA_OFFSET:
        return None
    if not payload.startswith(bytes.fromhex(PENGUIN_HEADER_HEX)):
        return None
    if payload[8:12].hex() != "b7000a00":
        return None

    channel, _sequence, total_parts, part_no, data_length = struct.unpack_from("<HHHHH", payload, 80)
    if channel != CALL_AUDIO_CHANNEL:
        return None
    if total_parts != 1 or part_no != 1:
        return None
    if data_length <= 0 or data_length % 2 != 0:
        return None
    if MONITOR_VIDEO_DATA_OFFSET + data_length > len(payload):
        return None

    return payload[MONITOR_VIDEO_DATA_OFFSET : MONITOR_VIDEO_DATA_OFFSET + data_length]


def build_session_header(
    command_hex: str,
    payload_length: int,
    device: Any,
    local_ip: str,
    local_id: str,
) -> bytes:
    return bytes.fromhex(
        "".join(
            [
                PENGUIN_HEADER_HEX,
                command_hex,
                "0000",
                _word_to_little_hex(payload_length),
                "00000000000000000000000000000000",
                _text_to_hex(f"S{local_id}"),
                PADDING_HEX,
                _ip_to_hex(local_ip),
                _text_to_hex(f"M000101{_device_value(device, 'door_no')}000"),
                PADDING_HEX,
                _ip_to_hex(_device_value(device, "target_ip")),
            ]
        )
    )


def build_monitor_discovery_payload(device: Any) -> bytes:
    device_id = f"M000101{_device_value(device, 'door_no')}000".encode("ascii")
    return b"\x01" + device_id + bytes(35 - 1 - len(device_id))


def build_monitor_request_payload(device: Any, local_ip: str, local_id: str) -> bytes:
    return (
        build_session_header("b8000100", 172, device, local_ip, local_id)
        + b"VIDEOA"
        + bytes.fromhex(MONITOR_VIDEO_TAIL_HEX)
    )


def build_monitor_start_payload(device: Any, local_ip: str, local_id: str) -> bytes:
    return build_session_header("b8000100", 80, device, local_ip, local_id)


def build_monitor_keepalive_payload(device: Any, local_ip: str, local_id: str) -> bytes:
    return build_session_header("b8000c00", 80, device, local_ip, local_id)


def monitor_broadcast_ip(local_ip: str) -> str:
    network = ipaddress.ip_network(f"{local_ip}/21", strict=False)
    return str(network.broadcast_address)


def parse_video_fragment(payload: bytes) -> VideoFragment | None:
    if len(payload) < MONITOR_VIDEO_DATA_OFFSET:
        return None
    if not payload.startswith(bytes.fromhex(PENGUIN_HEADER_HEX)):
        return None
    if payload[8:12].hex() not in VIDEO_FRAGMENT_COMMANDS:
        return None

    channel, frame_no, total_parts, part_no, data_length = struct.unpack_from("<HHHHH", payload, 80)
    if channel != 1:
        return None
    if total_parts < 1 or part_no < 1 or part_no > total_parts:
        return None
    if MONITOR_VIDEO_DATA_OFFSET + data_length > len(payload):
        return None

    return VideoFragment(
        frame_no=frame_no,
        total_parts=total_parts,
        part_no=part_no,
        data=payload[MONITOR_VIDEO_DATA_OFFSET : MONITOR_VIDEO_DATA_OFFSET + data_length],
    )


class MonitorFrameAssembler:
    def __init__(self) -> None:
        self._frames: dict[int, dict[str, Any]] = {}

    def add_packet(self, payload: bytes) -> bytes | None:
        fragment = parse_video_fragment(payload)
        if fragment is None:
            return None

        frame = self._frames.setdefault(
            fragment.frame_no,
            {"total_parts": fragment.total_parts, "parts": {}},
        )
        frame["parts"][fragment.part_no] = fragment.data

        if len(self._frames) > 30:
            for old_frame_no in sorted(self._frames)[:-30]:
                self._frames.pop(old_frame_no, None)

        if len(frame["parts"]) != fragment.total_parts:
            return None

        jpeg = b"".join(frame["parts"][part_no] for part_no in range(1, fragment.total_parts + 1))
        self._frames.pop(fragment.frame_no, None)
        if not jpeg.startswith(b"\xff\xd8") or not jpeg.endswith(b"\xff\xd9"):
            return None
        return jpeg


def _device_value(device: Any, key: str) -> str:
    if isinstance(device, dict):
        return str(device[key])
    return str(getattr(device, key))


def _text_to_hex(value: str) -> str:
    return value.encode("ascii").hex()


def _ip_to_hex(ip_address: str) -> str:
    return socket.inet_aton(ip_address).hex()


def _word_to_little_hex(value: int) -> str:
    return value.to_bytes(2, "little").hex()
