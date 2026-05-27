from pathlib import Path
import unittest


REPO_DIR = Path(__file__).resolve().parents[1]
ADDON_DIR = REPO_DIR / "addons" / "uppercoast_doorlock"


class AddonMetadataTest(unittest.TestCase):
    def test_addon_display_name_and_version_are_declared(self):
        config_text = (ADDON_DIR / "config.yaml").read_text(encoding="utf-8")

        self.assertIn('name: "门禁系统后端"', config_text)
        self.assertIn('version: "0.1.0"', config_text)
        self.assertIn('slug: "uppercoast_doorlock"', config_text)
        self.assertIn('description: "仅支持麦驰可视对讲门禁系统；运行虚拟室内机、呼叫监听、接听和解锁服务。"', config_text)

    def test_addon_changelog_exists_for_home_assistant_store(self):
        changelog = ADDON_DIR / "CHANGELOG.md"

        self.assertTrue(changelog.exists())
        changelog_text = changelog.read_text(encoding="utf-8")
        self.assertIn("## 0.1.0 - 2026-05-27", changelog_text)
        self.assertIn("麦驰可视对讲门禁系统", changelog_text)
        self.assertEqual(1, changelog_text.count("## 0.1.0 - 2026-05-27"))

    def test_addon_readme_is_chinese_first(self):
        readme_text = (ADDON_DIR / "README.md").read_text(encoding="utf-8")

        self.assertIn("这个加载项运行虚拟室内机、呼叫监听、接听和解锁服务", readme_text)
        self.assertIn("麦驰可视对讲门禁系统", readme_text)
        self.assertIn("主机网络模式", readme_text)

    def test_simplified_chinese_configuration_translation_exists(self):
        translation = ADDON_DIR / "translations" / "zh-Hans.yaml"
        translation_text = translation.read_text(encoding="utf-8")

        self.assertIn("门禁网本机 IP", translation_text)
        self.assertIn("1号机 IP 覆盖", translation_text)


if __name__ == "__main__":
    unittest.main()
