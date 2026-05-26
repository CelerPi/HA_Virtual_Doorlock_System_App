from __future__ import annotations

import json
import os
import time
from pathlib import Path

from .api import ApiServer
from .core import IntercomCore
from .config import load_addon_options
from .store import ConfigStore


def main() -> None:
    options_path = Path(os.environ.get("YUNHAI_OPTIONS_PATH", "/data/options.json"))
    store_path = Path(os.environ.get("YUNHAI_CONFIG_PATH", "/data/yunhai_config.json"))
    defaults = load_addon_options(options_path)
    config = ConfigStore(store_path).load(defaults)
    core = IntercomCore(config)
    api_server = ApiServer(core, config)
    core.start()
    api_server.start()
    print(
        json.dumps(
            {
                "event": "yunhai_intercom_started",
                "config": config.as_dict(),
                "store_path": str(store_path),
                "api_url": f"http://{config.api_host}:{config.api_port}",
            },
            ensure_ascii=False,
        ),
        flush=True,
    )

    try:
        while True:
            time.sleep(60)
    finally:
        api_server.stop()
        core.stop()


if __name__ == "__main__":
    main()
