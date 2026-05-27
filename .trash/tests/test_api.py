import io
import json
import sys
import unittest
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1] / "addons" / "uppercoast_doorlock" / "app"
sys.path.insert(0, str(APP_DIR))

from uppercoast_doorlock.api import make_api_handler
from uppercoast_doorlock.config import normalize_options


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
        self.handler_cls = make_api_handler(self.core, self.config)

    def test_health_endpoint_returns_ok(self):
        response = self._invoke("GET", "/health")

        self.assertEqual(200, response["status"])
        self.assertEqual({"ok": True}, response["json"])

    def test_status_endpoint_returns_runtime_and_config_summary(self):
        response = self._invoke("GET", "/api/status")

        self.assertEqual("持续监听 192.168.16.64:10000，等待室外机呼叫", response["json"]["runtime"]["status"])
        self.assertTrue(response["json"]["runtime"]["in_call"])
        self.assertEqual("192.168.16.225", response["json"]["runtime"]["target_ip"])
        self.assertEqual("building_1_a", response["json"]["config"]["building_id"])
        self.assertEqual(8, response["json"]["config"]["active_device_count"])

    def test_unlock_requires_bearer_token(self):
        response = self._invoke("POST", "/api/unlock", {"target_ip": "192.168.16.225"})

        self.assertEqual(403, response["status"])
        self.assertEqual({"ok": False, "error": "forbidden"}, response["json"])
        self.assertEqual([], self.core.unlock_targets)

    def test_unlock_and_answer_actions_use_current_target_by_default(self):
        unlock = self._invoke("POST", "/api/unlock", headers={"Authorization": "Bearer secret-token"})
        answer = self._invoke("POST", "/api/answer", headers={"Authorization": "Bearer secret-token"})

        self.assertEqual(200, unlock["status"])
        self.assertTrue(unlock["json"]["ok"])
        self.assertTrue(answer["json"]["ok"])
        self.assertEqual(["192.168.16.225"], self.core.unlock_targets)
        self.assertEqual(["192.168.16.225"], self.core.answer_targets)

    def test_action_returns_conflict_when_core_rejects_request(self):
        response = self._invoke(
            "POST",
            "/api/unlock",
            {"target_ip": "192.168.16.226"},
            {"Authorization": "Bearer secret-token"},
        )

        self.assertEqual(409, response["status"])
        self.assertEqual({"ok": False, "error": "request_rejected", "action": "unlock"}, response["json"])

    def _invoke(self, method, path, body=None, headers=None):
        handler = self.handler_cls.__new__(self.handler_cls)
        handler.path = path
        payload = b"" if body is None else json.dumps(body).encode("utf-8")
        handler.headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(payload)),
            **(headers or {}),
        }
        handler.rfile = io.BytesIO(payload)
        handler.wfile = io.BytesIO()
        handler.responses = []
        handler.send_response = lambda status: handler.responses.append(status)
        handler.send_header = lambda *_args, **_kwargs: None
        handler.end_headers = lambda: None

        getattr(handler, f"do_{method}")()
        payload = handler.wfile.getvalue().decode("utf-8")
        return {
            "status": handler.responses[0],
            "json": json.loads(payload),
        }


if __name__ == "__main__":
    unittest.main()
