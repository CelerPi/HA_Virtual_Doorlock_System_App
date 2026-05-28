from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_LOCAL_IP = "192.168.16.64"
DEFAULT_LOCAL_ID = "00010116010"
DEFAULT_BUILDING_ID = "building_1_a"
DEFAULT_CENTER_IP = "192.168.16.2"
DEFAULT_PROPERTY_CENTER_IP = "192.168.16.3"
DEFAULT_API_HOST = "0.0.0.0"
DEFAULT_API_PORT = 8099
DEFAULT_API_TOKEN = "1234"

DOOR_IP_OPTION_BY_DOOR = {
    "01": "door_01_ip",
    "02": "door_02_ip",
    "03": "door_03_ip",
    "04": "door_04_ip",
    "05": "door_05_ip",
    "06": "door_06_ip",
    "07": "door_07_ip",
    "08": "door_08_ip",
}

BUILDING_NAMES = [
    ("building_1_a", "1栋A座"),
    ("building_1_b", "1栋B座"),
    ("building_1_c", "1栋C座"),
    ("building_1_d", "1栋D座"),
    ("building_1_e", "1栋E座"),
    ("building_2_a", "2栋A座"),
    ("building_2_b", "2栋B座"),
    ("building_2_c", "2栋C座"),
]

BUILDING_NAME_BY_ID = dict(BUILDING_NAMES)
BUILDING_ID_BY_NAME = {name: building_id for building_id, name in BUILDING_NAMES}

STATION_LAYOUT_BY_DOOR = {
    "01": {"name": "1F-1", "floor_label": "1层", "position_detail": "未知"},
    "02": {"name": "2F-2", "floor_label": "2层", "position_detail": "未知"},
    "03": {"name": "B1-3", "floor_label": "-1层", "position_detail": "未知"},
    "04": {"name": "B2-4", "floor_label": "-2层", "position_detail": "未知"},
    "05": {"name": "1F-5", "floor_label": "-1层", "position_detail": "未知"},
    "06": {"name": "1F-6", "floor_label": "-1层", "position_detail": "未知"},
    "07": {"name": "1F-7", "floor_label": "-2层", "position_detail": "未知"},
    "08": {"name": "1F-8", "floor_label": "1层", "position_detail": "未知"},
}

BUILDING_POSITION_OVERRIDES = {
    "building_1_a": {
        "01": "车库",
        "02": "花园",
        "03": "车库",
        "04": "车库",
        "05": "电梯左侧小门左边",
        "06": "电梯左侧小门右边",
        "07": "电梯左侧小门左边",
        "08": "电梯正对",
    }
}

BUILDING_IPS_BY_ID = {
    "building_1_a": {
        "01": "192.168.16.224",
        "02": "192.168.16.225",
        "03": "192.168.16.226",
        "04": "192.168.16.227",
        "05": "192.168.16.228",
        "06": "192.168.16.229",
        "07": "192.168.23.162",
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


@dataclass(frozen=True)
class DoorStation:
    name: str
    door_no: str
    floor_label: str
    position_detail: str
    target_ip: str = ""

    @property
    def display_name(self) -> str:
        return f"{int(self.door_no)}号机"

    def as_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "door_no": self.door_no,
            "floor_label": self.floor_label,
            "position_detail": self.position_detail,
            "target_ip": self.target_ip,
        }


@dataclass(frozen=True)
class IntercomConfig:
    local_ip: str
    local_id: str
    building_id: str
    building_name: str
    center_ip: str
    property_center_ip: str
    api_host: str
    api_port: int
    api_token: str
    devices: tuple[DoorStation, ...]

    @property
    def active_devices(self) -> list[DoorStation]:
        return [device for device in self.devices if device.target_ip]

    def as_dict(self, include_secret: bool = False) -> dict[str, Any]:
        data = {
            "local_ip": self.local_ip,
            "local_id": self.local_id,
            "building_id": self.building_id,
            "building_name": self.building_name,
            "center_ip": self.center_ip,
            "property_center_ip": self.property_center_ip,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "devices": [device.as_dict() for device in self.devices],
            "active_device_count": len(self.active_devices),
        }
        if include_secret:
            data["api_token"] = self.api_token
        return data


def load_addon_options(options_path: str | Path = "/data/options.json") -> IntercomConfig:
    path = Path(options_path)
    if path.exists():
        raw_options = json.loads(path.read_text(encoding="utf-8"))
    else:
        raw_options = {}
    return normalize_options(raw_options)


def normalize_options(raw_options: Any) -> IntercomConfig:
    options = raw_options if isinstance(raw_options, dict) else {}

    building_value = str(options.get("building_id") or DEFAULT_BUILDING_ID).strip()
    building_id = BUILDING_ID_BY_NAME.get(building_value, building_value)
    if building_id not in BUILDING_NAME_BY_ID:
        building_id = DEFAULT_BUILDING_ID

    devices = tuple(_build_devices(building_id, options.get("devices"), options))

    return IntercomConfig(
        local_ip=str(options.get("local_ip") or DEFAULT_LOCAL_IP),
        local_id=str(options.get("local_id") or DEFAULT_LOCAL_ID),
        building_id=building_id,
        building_name=BUILDING_NAME_BY_ID[building_id],
        center_ip=str(options.get("center_ip") or DEFAULT_CENTER_IP),
        property_center_ip=str(options.get("property_center_ip") or DEFAULT_PROPERTY_CENTER_IP),
        api_host=str(options.get("api_host") or DEFAULT_API_HOST),
        api_port=_coerce_api_port(options.get("api_port")),
        api_token=str(options.get("api_token") or DEFAULT_API_TOKEN),
        devices=devices,
    )


def _build_devices(
    building_id: str,
    saved_devices: Any = None,
    raw_options: dict[str, Any] | None = None,
) -> list[DoorStation]:
    known_ips = BUILDING_IPS_BY_ID.get(building_id, {})
    position_overrides = BUILDING_POSITION_OVERRIDES.get(building_id, {})
    saved_by_door = _saved_devices_by_door(saved_devices)
    option_ip_overrides = _door_ip_overrides(raw_options)
    devices = []

    for door_no, default_target_ip in known_ips.items():
        station = STATION_LAYOUT_BY_DOOR[door_no]
        saved = saved_by_door.get(door_no, {})
        saved_target_ip = saved.get("target_ip")
        target_ip = option_ip_overrides.get(door_no)
        if target_ip is None:
            target_ip = saved_target_ip if saved_target_ip is not None else default_target_ip
        default_position_detail = position_overrides.get(door_no, station["position_detail"])
        devices.append(
            DoorStation(
                name=str(saved.get("name") or station["name"]),
                door_no=door_no,
                floor_label=str(saved.get("floor_label") or station["floor_label"]),
                position_detail=str(saved.get("position_detail") or default_position_detail),
                target_ip=str(target_ip),
            )
        )

    return devices


def _door_ip_overrides(raw_options: dict[str, Any] | None) -> dict[str, str]:
    if not raw_options:
        return {}

    overrides = {}
    for door_no, option_key in DOOR_IP_OPTION_BY_DOOR.items():
        value = str(raw_options.get(option_key) or "").strip()
        if value:
            overrides[door_no] = value
    return overrides


def _saved_devices_by_door(saved_devices: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(saved_devices, list):
        return {}

    devices: dict[str, dict[str, Any]] = {}
    for device in saved_devices:
        if not isinstance(device, dict):
            continue
        door_no = str(device.get("door_no") or "").strip()
        if door_no:
            devices[door_no] = device
    return devices


def _coerce_api_port(value: Any) -> int:
    try:
        port = int(value)
    except (TypeError, ValueError):
        return DEFAULT_API_PORT
    if port < 1 or port > 65535:
        return DEFAULT_API_PORT
    return port
