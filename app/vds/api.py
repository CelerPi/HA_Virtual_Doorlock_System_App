from __future__ import annotations

import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .config import IntercomConfig


def make_api_handler(core: Any, config: IntercomConfig) -> type[BaseHTTPRequestHandler]:
    class VDSApiHandler(BaseHTTPRequestHandler):
        server_version = "VDS-API/0.1.0"

        def do_GET(self) -> None:
            if self.path == "/health":
                self._write_json(200, {"ok": True})
                return
            if self.path == "/api/status":
                self._write_json(
                    200,
                    {
                        "runtime": core.frame_hub.snapshot(),
                        "config": config.as_dict(),
                    },
                )
                return
            if self.path == "/api/frame":
                frame = core.frame_hub.get_frame()
                if frame is None:
                    self._write_json(404, {"ok": False, "error": "no_frame"})
                    return
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(frame)))
                self.end_headers()
                self.wfile.write(frame)
                return
            if self.path.startswith("/api/audio"):
                if not self._authorized():
                    self._write_json(403, {"ok": False, "error": "forbidden"})
                    return
                since = 0
                if "?" in self.path:
                    query = self.path.split("?", 1)[1]
                    for param in query.split("&"):
                        if param.startswith("since="):
                            try:
                                since = int(param.split("=", 1)[1])
                            except (ValueError, IndexError):
                                pass
                chunks = core.frame_hub.get_audio_chunks(since)
                self._write_json(200, {
                    "ok": True,
                    "audio_id": core.frame_hub.snapshot().get("audio_id", 0),
                    "chunks": [
                        {"id": aid, "pcm": base64.b64encode(pcm).decode("ascii")}
                        for aid, pcm in chunks
                    ],
                })
                return
            if self.path.startswith("/api/monitor/"):
                parts = self.path.split("/")
                if len(parts) == 4 and parts[3] in ("start", "stop"):
                    action = parts[3]
                    body = self._read_json()
                    target_ip = body.get("target_ip", "").strip()
                    if not target_ip:
                        self._write_json(400, {"ok": False, "error": "missing_target_ip"})
                        return
                    if action == "start":
                        accepted = core.request_monitor_start(str(target_ip))
                    else:
                        accepted = core.request_monitor_stop(str(target_ip))
                    if not accepted:
                        self._write_json(409, {"ok": False, "error": "monitor_request_rejected"})
                        return
                    self._write_json(200, {"ok": True, "action": action, "target_ip": target_ip})
                    return
            self._write_json(404, {"ok": False, "error": "not_found"})

        def do_POST(self) -> None:
            if self.path in ("/api/unlock", "/api/answer", "/api/hangup"):
                if not self._authorized():
                    self._write_json(403, {"ok": False, "error": "forbidden"})
                    return

                body = self._read_json()
                target_ip = body.get("target_ip") or core.frame_hub.snapshot().get("target_ip")
                if not target_ip:
                    self._write_json(409, {"ok": False, "error": "no_active_call"})
                    return

                if self.path == "/api/unlock":
                    accepted = core.request_unlock(str(target_ip))
                    action = "unlock"
                elif self.path == "/api/answer":
                    accepted = core.request_answer(str(target_ip))
                    action = "answer"
                else:
                    accepted = core.request_hangup(str(target_ip))
                    action = "hangup"

                if not accepted:
                    self._write_json(409, {"ok": False, "error": "request_rejected", "action": action})
                    return
                self._write_json(200, {"ok": True, "action": action, "target_ip": target_ip})
                return

            if self.path == "/api/audio":
                if not self._authorized():
                    self._write_json(403, {"ok": False, "error": "forbidden"})
                    return

                body = self._read_json()
                target_ip = body.get("target_ip", "").strip()
                pcm_b64 = body.get("pcm", "")
                if not target_ip or not pcm_b64:
                    self._write_json(400, {"ok": False, "error": "missing_target_ip_or_pcm"})
                    return

                try:
                    pcm = base64.b64decode(pcm_b64)
                except Exception:
                    self._write_json(400, {"ok": False, "error": "invalid_pcm_base64"})
                    return

                if len(pcm) % 2 != 0:
                    self._write_json(400, {"ok": False, "error": "pcm_length_must_be_even"})
                    return

                accepted = core.request_outgoing_audio(target_ip, pcm)
                if not accepted:
                    self._write_json(409, {"ok": False, "error": "audio_request_rejected"})
                    return
                self._write_json(200, {"ok": True, "target_ip": target_ip, "samples": len(pcm) // 2})
                return

            if self.path in ("/api/monitor/start", "/api/monitor/stop"):
                if not self._authorized():
                    self._write_json(403, {"ok": False, "error": "forbidden"})
                    return

                body = self._read_json()
                target_ip = body.get("target_ip", "").strip()
                if not target_ip:
                    self._write_json(400, {"ok": False, "error": "missing_target_ip"})
                    return

                action = "start" if self.path == "/api/monitor/start" else "stop"
                if action == "start":
                    accepted = core.request_monitor_start(str(target_ip))
                else:
                    accepted = core.request_monitor_stop(str(target_ip))

                if not accepted:
                    self._write_json(409, {"ok": False, "error": "monitor_request_rejected"})
                    return
                self._write_json(200, {"ok": True, "action": action, "target_ip": target_ip})
                return

            self._write_json(404, {"ok": False, "error": "not_found"})

        def log_message(self, _format: str, *_args: Any) -> None:
            return

        def _authorized(self) -> bool:
            if not config.api_token:
                return False
            return self.headers.get("Authorization", "") == f"Bearer {config.api_token}"

        def _read_json(self) -> dict[str, Any]:
            content_length = int(self.headers.get("Content-Length") or 0)
            if content_length <= 0:
                return {}
            try:
                payload = self.rfile.read(content_length)
                data = json.loads(payload.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return {}
            return data if isinstance(data, dict) else {}

        def _write_json(self, status: int, body: dict[str, Any]) -> None:
            payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    return VDSApiHandler


class ApiServer:
    def __init__(self, core: Any, config: IntercomConfig) -> None:
        self.core = core
        self.config = config
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._server is not None:
            return
        handler = make_api_handler(self.core, self.config)
        self._server = ThreadingHTTPServer((self.config.api_host, self.config.api_port), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, name="VDS-API", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)
        self._server = None
        self._thread = None
