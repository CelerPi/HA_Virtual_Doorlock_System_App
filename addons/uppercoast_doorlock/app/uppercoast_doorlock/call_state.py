from __future__ import annotations

from dataclasses import dataclass

from .config import DoorStation, IntercomConfig


CALL_TRIGGER_COMMANDS = ("cd000100", "98000100", "b7000100")
CALL_END_COMMANDS = ("b4000600",)


@dataclass(frozen=True)
class CallEvent:
    kind: str
    command: str
    device: DoorStation


def devices_by_ip(config: IntercomConfig) -> dict[str, DoorStation]:
    return {device.target_ip: device for device in config.active_devices}


def parse_penguin_command(payload: bytes) -> str:
    if payload.startswith(b"PENGUIN0") and len(payload) >= 12:
        return payload[8:12].hex()
    return "-"


class CallStateTracker:
    def __init__(self, config: IntercomConfig) -> None:
        self._devices_by_ip = devices_by_ip(config)
        self._current_device: DoorStation | None = None

    def handle_packet(self, payload: bytes, address: tuple[str, int]) -> CallEvent | None:
        source_ip = address[0]
        device = self._devices_by_ip.get(source_ip)
        if device is None:
            print(f"[call_state] 丢弃: 源IP {source_ip} 不在已知门口机列表中。已知: {list(self._devices_by_ip.keys())}", flush=True)
            return None

        command = parse_penguin_command(payload)
        print(f"[call_state] 匹配设备: {device.display_name}({device.target_ip}) 命令: {command}", flush=True)
        if command in CALL_TRIGGER_COMMANDS:
            self._current_device = device
            return CallEvent("call_started", command, device)

        if command in CALL_END_COMMANDS and self._current_device == device:
            self._current_device = None
            return CallEvent("call_ended", command, device)

        return None

    def snapshot(self) -> dict[str, str | bool]:
        if self._current_device is None:
            return {
                "in_call": False,
                "device_name": "",
                "display_name": "",
                "target_ip": "",
                "floor_label": "",
                "position_detail": "",
            }

        return {
            "in_call": True,
            "device_name": self._current_device.name,
            "display_name": self._current_device.display_name,
            "target_ip": self._current_device.target_ip,
            "floor_label": self._current_device.floor_label,
            "position_detail": self._current_device.position_detail,
        }
