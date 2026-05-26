import json
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


APP_DIR = Path(__file__).resolve().parents[1] / "addons" / "yunhai_intercom" / "app"
sys.path.insert(0, str(APP_DIR))

from yunhai_intercom.api import make_api_handler
from yunhai_intercom.config import normalize_options


class FakeFrameHub:
    def snapshot(self):
        return {
            "status": "持续监听 192.168.16.64:10000，等待室外机呼叫",
            "in_call": True,
            "device_name": "2F-2",
            "display_name": "2号机",
            "target_ip": "192.168.16.225",
            "has_frame": False,
            "has_audio": False,
        }


class FakeCore:
    def __init__(self):
        self.frame_hub = FakeFrameHub()
        self.unlock_targets = []
        self.answer_targets = []

    def request_unlock(self, target_ip):
        self.unlock_targets.append(target_ip)
        return target_ip == "192.168.16.225"

    def request_answer(self, target_ip):
        self.answer_targets.append(target_ip)
        return target_ip == "192.168.16.225"


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.config = normalize_options(
            {
                "api_token": "secret-token",
                "api_host": "127.0.0.1",
                "api_port": 0,
            }
        )
        self.core = FakeCore()
        handler = make_api_handler(self.core, self.config)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_health_endpoint_returns_ok(self):
        response = self._json("GET", "/health")

        self.assertEqual({"ok": True}, response)

    def test_status_endpoint_returns_runtime_and_config_summary(self):
        response = self._json("GET", "/api/status")

        self.assertEqual("持续监听 192.168.16.64:10000，等待室外机呼叫", response["runtime"]["status"])
        self.assertTrue(response["runtime"]["in_call"])
        self.assertEqual("192.168.16.225", response["runtime"]["target_ip"])
        self.assertEqual("building_1_a", response["config"]["building_id"])
        self.assertEqual(8, response["config"]["active_device_count"])

    def test_unlock_requires_bearer_token(self):
        with self.assertRaises(HTTPError) as error:
            self._json("POST", "/api/unlock", {"target_ip": "192.168.16.225"})

        self.assertEqual(403, error.exception.code)
        error.exception.close()
        self.assertEqual([], self.core.unlock_targets)

    def test_unlock_and_answer_actions_use_current_target_by_default(self):
        unlock = self._json("POST", "/api/unlock", headers={"Authorization": "Bearer secret-token"})
        answer = self._json("POST", "/api/answer", headers={"Authorization": "Bearer secret-token"})

        self.assertTrue(unlock["ok"])
        self.assertTrue(answer["ok"])
        self.assertEqual(["192.168.16.225"], self.core.unlock_targets)
        self.assertEqual(["192.168.16.225"], self.core.answer_targets)

    def test_action_returns_conflict_when_core_rejects_request(self):
        with self.assertRaises(HTTPError) as error:
            self._json(
                "POST",
                "/api/unlock",
                {"target_ip": "192.168.16.226"},
                {"Authorization": "Bearer secret-token"},
            )

        self.assertEqual(409, error.exception.code)
        error.exception.close()

    def _json(self, method, path, body=None, headers=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(
            self.base_url + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json", **(headers or {})},
        )
        with urlopen(request, timeout=2) as response:
            return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
