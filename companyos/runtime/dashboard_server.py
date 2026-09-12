from __future__ import annotations

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = (Path.home() / "companyos").resolve()
RUNTIME = ROOT / ".companyos_runtime"
RUNTIME.mkdir(parents=True, exist_ok=True)

HOST = os.getenv("COMPANYOS_DASHBOARD_HOST", "127.0.0.1")
PORT = int(os.getenv("COMPANYOS_DASHBOARD_PORT", "8765"))
TOKEN = os.getenv("COMPANYOS_DASHBOARD_TOKEN", "")

if HOST not in {"127.0.0.1", "localhost", "::1"} and not TOKEN:
    raise SystemExit(
        "Refusing non-local dashboard bind without COMPANYOS_DASHBOARD_TOKEN"
    )


def _json_bytes(obj):
    return json.dumps(obj, indent=2, sort_keys=True, default=str).encode("utf-8")


def _authorized(handler):
    if not TOKEN:
        return True
    supplied = handler.headers.get("X-CompanyOS-Token", "")
    return supplied == TOKEN


def _status():
    from companyos.runtime.runtime_control import UnifiedRuntimeControl
    from companyos.runtime.launch_readiness import LaunchReadinessAudit
    from companyos.runtime.connector_readiness import ConnectorReadinessAudit

    ctl = UnifiedRuntimeControl(ROOT)
    return {
        "checked_at_unix": time.time(),
        "health": ctl.health(),
        "launch_readiness": LaunchReadinessAudit(ROOT).run(),
        "connectors": ConnectorReadinessAudit(ROOT).run(),
    }


HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CompanyOS Control</title>
<style>
body{font-family:system-ui;margin:18px;background:#111;color:#eee}
button{margin:4px;padding:12px 16px;font-size:16px}
pre{white-space:pre-wrap;background:#1d1d1d;padding:12px;border-radius:8px;overflow:auto}
.ok{color:#76e08a}.bad{color:#ff7c7c}
</style>
</head>
<body>
<h1>CompanyOS</h1>
<div>
<button onclick="act('start')">Start</button>
<button onclick="act('stop')">Stop</button>
<button onclick="act('restart')">Restart</button>
<button onclick="act('recover')">Recover</button>
<button onclick="refresh()">Refresh</button>
</div>
<h2 id="headline">Loading…</h2>
<pre id="out"></pre>
<script>
async function refresh(){
  const r=await fetch('/api/status');
  const j=await r.json();
  const healthy=!!(j.health&&j.health.healthy);
  document.getElementById('headline').innerHTML =
    healthy ? '<span class="ok">Runtime healthy</span>' :
              '<span class="bad">Runtime needs attention</span>';
  document.getElementById('out').textContent=JSON.stringify(j,null,2);
}
async function act(name){
  await fetch('/api/control/'+name,{method:'POST'});
  setTimeout(refresh,700);
}
refresh(); setInterval(refresh,5000);
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "CompanyOSDashboard/1.0"

    def log_message(self, fmt, *args):
        path = RUNTIME / "dashboard_http.log"
        with path.open("a", encoding="utf-8") as f:
            f.write(
                f"{time.strftime('%Y-%m-%d %H:%M:%S')} "
                + (fmt % args)
                + "\n"
            )

    def _send_json(self, code, obj):
        data = _json_bytes(obj)
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            data = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if path in {"/api/status", "/api/health"}:
            if not _authorized(self):
                self._send_json(401, {"ok": False, "error": "unauthorized"})
                return
            self._send_json(200, _status())
            return

        self._send_json(404, {"ok": False, "error": "not_found"})

    def do_POST(self):
        if not _authorized(self):
            self._send_json(401, {"ok": False, "error": "unauthorized"})
            return

        path = urlparse(self.path).path
        prefix = "/api/control/"
        if not path.startswith(prefix):
            self._send_json(404, {"ok": False, "error": "not_found"})
            return

        action = path[len(prefix):]
        from companyos.runtime.runtime_control import UnifiedRuntimeControl

        ctl = UnifiedRuntimeControl(ROOT)
        if action == "start":
            result = ctl.start()
        elif action == "stop":
            result = ctl.stop()
        elif action == "restart":
            result = ctl.restart()
        elif action == "recover":
            result = ctl.recover()
        else:
            self._send_json(
                400, {"ok": False, "error": f"unsupported_action:{action}"}
            )
            return

        self._send_json(200 if result.get("ok") else 500, result)


def main():
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    state = {
        "host": HOST,
        "port": PORT,
        "url": f"http://{HOST}:{PORT}/",
        "pid": os.getpid(),
        "started_at_unix": time.time(),
    }
    (RUNTIME / "dashboard_server_state.json").write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    httpd.serve_forever(poll_interval=0.5)


if __name__ == "__main__":
    main()
