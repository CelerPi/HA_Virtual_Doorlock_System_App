from __future__ import annotations

import json
from pathlib import Path

from .config import IntercomConfig, normalize_options


OPTION_CONTROLLED_KEYS = (
    "local_ip",
    "local_id",
    "building_id",
    "center_ip",
    "property_center_ip",
)


class ConfigStore:
    def __init__(self, path: str | Path = "/data/yunhai_config.json") -> None:
        self.path = Path(path)

    def load(self, defaults: IntercomConfig) -> IntercomConfig:
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            raw = {}

        merged = dict(raw) if isinstance(raw, dict) else {}
        default_data = defaults.as_dict()
        if merged.get("building_id") != default_data["building_id"]:
            merged.pop("devices", None)
        for key in OPTION_CONTROLLED_KEYS:
            merged[key] = default_data[key]
        if "devices" not in merged:
            merged["devices"] = default_data["devices"]

        config = normalize_options(merged)
        self.save(config)
        return config

    def save(self, config: IntercomConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(config.as_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
