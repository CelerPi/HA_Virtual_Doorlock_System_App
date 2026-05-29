from __future__ import annotations

import os
import time
from pathlib import Path

from .api import ApiServer
from .core import IntercomCore
from .config import load_addon_options
from .store import ConfigStore


SUPPORTED_BRAND = "麦驰可视对讲门禁系统"


def main() -> None:
    options_path = Path(os.environ.get("UPPERCOAST_OPTIONS_PATH", "/data/options.json"))
    store_path = Path(os.environ.get("UPPERCOAST_CONFIG_PATH", "/data/uppercoast_config.json"))
    defaults = load_addon_options(options_path)
    config = ConfigStore(store_path).load(defaults)
    core = IntercomCore(config)
    api_server = ApiServer(core, config)
    core.start()
    api_server.start()
    _print_startup_summary(config, store_path)

    try:
        while True:
            time.sleep(60)
    finally:
        api_server.stop()
        core.stop()


def _print_startup_summary(config, store_path: Path) -> None:
    for line in _startup_summary_lines(config, store_path):
        print(line, flush=True)


def _startup_summary_lines(config, store_path: Path) -> list[str]:
    devices = "、".join(f"{device.display_name}={device.target_ip}" for device in config.active_devices)
    return [
        "门禁系统后端已启动",
        f"支持品牌：{SUPPORTED_BRAND}",
        f"楼栋：{config.building_name}；已加载门口机：{len(config.active_devices)} 个",
        f"本机 IP：{config.local_ip}；室内机 ID：{config.local_id}",
        f"中心地址：{config.center_ip}；物业中心机：{config.property_center_ip}",
        f"后端接口：http://{config.api_host}:{config.api_port}",
        f"运行时配置：{store_path}",
        f"门口机列表：{devices or '无可用门口机'}",
    ]


if __name__ == "__main__":
    main()
