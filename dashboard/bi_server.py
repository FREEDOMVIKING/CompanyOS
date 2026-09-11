#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path.home() / "companyos"
DASHBOARD = ROOT / "dashboard"
SNAPSHOT = ROOT / "ceo_memory" / "business_intelligence_snapshot.json"
BICTL = ROOT / "companyos" / "bictl"


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        relative = urlparse(path).path.lstrip("/") or "index.html"
        return str(DASHBOARD / relative)

    def send_json(self, value: object, status: int = 200) -> None:
        body = json.dumps(value, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/api/snapshot":
            try:
                data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
                self.send_json(data)
            except Exception as exc:
                self.send_json(
                    {"success": False, "error": str(exc)},
                    500,
                )
            return

        super().do_GET()

    def do_POST(self) -> None:
        if urlparse(self.path).path == "/api/refresh":
            result = subprocess.run(
                [sys.executable, str(BICTL), "generate"],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

            try:
                payload = json.loads(result.stdout)
            except Exception:
                payload = {
                    "success": False,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }

            self.send_json(
                payload,
                200 if result.returncode == 0 else 500,
            )
            return

        self.send_json({"success": False, "error": "not_found"}, 404)


def main() -> None:
    host = "127.0.0.1"
    port = 8781
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Open http://{host}:{port}")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
