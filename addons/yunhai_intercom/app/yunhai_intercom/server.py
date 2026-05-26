from __future__ import annotations

import json
import os
import time
from pathlib import Path

from .core import IntercomCore
from .config import load_addon_options
from .store import ConfigStore


def main() -> None:
    options_path = Path(os.environ.get("YUNHAI_OPTIONS_PATH", "/data/options.json"))
    store_path = Path(os.environ.get("YUNHAI_CONFIG_PATH", "/data/yunhai_config.json"))
    defaults = load_addon_options(options_path)
    config = ConfigStore(store_path).load(defaults)
    core = IntercomCore(config)
    core.start()
    print(
        json.dumps(
            {
                "event": "yunhai_intercom_started",
                "config": config.as_dict(),
                "store_path": str(store_path),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )

    try:
        while True:
            time.sleep(60)
    finally:
        core.stop()


if __name__ == "__main__":
    main()
