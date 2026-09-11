#!/usr/bin/env python3
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import request, error

HOST = "127.0.0.1"
PORT = 8765

PROVIDER_URL = os.getenv("COMPANYOS_PROVIDER_URL", "")
PROVIDER_API_KEY = os.getenv("COMPANYOS_PROVIDER_API_KEY", "")
PROVIDER_MODEL = os.getenv("COMPANYOS_PROVIDER_MODEL", "openrouter/auto")

class Handler(BaseHTTPRequestHandler):
    def _send(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/reason":
            self._send(404, {"success": False, "error": "not_found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length) or b"{}")
        except Exception as exc:
            self._send(400, {"success": False, "error": "invalid_json", "message": str(exc)})
            return

        if not PROVIDER_URL:
            self._send(200, {
                "success": True,
                "mode": "gateway_fallback",
                "message": "Gateway live; external provider not configured.",
                "received": data
            })
            return

        # OpenAI/OpenRouter compatible payload translation.
        if isinstance(data, dict) and "messages" in data:
            payload = dict(data)
            payload["model"] = PROVIDER_MODEL or data.get("model", "openrouter/auto")
            payload.pop("metadata", None)
        else:
            payload = {
                "model": PROVIDER_MODEL,
                "messages": [{
                    "role": "user",
                    "content": json.dumps(data, default=str)
                }]
            }

        headers = {"Content-Type": "application/json"}
        if PROVIDER_API_KEY:
            headers["Authorization"] = f"Bearer {PROVIDER_API_KEY}"
        headers["X-Title"] = "CompanyOS Autonomous CEO"

        req = request.Request(
            PROVIDER_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        try:
            with request.urlopen(req, timeout=90) as resp:
                raw = resp.read().decode("utf-8", "replace")
                try:
                    result = json.loads(raw)
                except Exception:
                    result = {"raw": raw}
                self._send(200, {
                    "success": True,
                    "mode": "external_provider",
                    "provider_response": result
                })
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", "replace")
            self._send(502, {
                "success": False,
                "error": "provider_http_error",
                "status_code": exc.code,
                "details": details[:4000]
            })
        except Exception as exc:
            self._send(502, {
                "success": False,
                "error": type(exc).__name__,
                "message": str(exc)
            })

    def log_message(self, fmt, *args):
        return

if __name__ == "__main__":
    print(f"COMPANYOS_REASONING_GATEWAY_READY http://{HOST}:{PORT}/reason")
    HTTPServer((HOST, PORT), Handler).serve_forever()
