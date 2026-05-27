import sys
import unittest
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1] / "addons" / "uppercoast_doorlock" / "app"
sys.path.insert(0, str(APP_DIR))

from uppercoast_doorlock.config import normalize_options
from uppercoast_doorlock.server import _startup_summary_lines


class ServerLogTest(unittest.TestCase):
    def test_startup_summary_is_short_chinese_text(self):
        config = normalize_options({"building_id": "1栋A座"})

        lines = _startup_summary_lines(config, Path("/data/uppercoast_config.json"))
        text = "\n".join(lines)

        self.assertIn("门禁系统后端已启动", text)
        self.assertIn("支持品牌：麦驰可视对讲门禁系统", text)
        self.assertIn("楼栋：1栋A座；已加载门口机：8 个", text)
        self.assertIn("门口机列表：1号机=192.168.16.224", text)
        self.assertNotIn('"devices"', text)
        self.assertLessEqual(len(lines), 8)


if __name__ == "__main__":
    unittest.main()
