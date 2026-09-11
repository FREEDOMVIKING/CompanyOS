
import json
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HOST = "127.0.0.1"
PORT = 8780

SERVICES = [
    ("Master Controls", 8766, "/"),
    ("Venture Progress", 8767, "/"),
    ("Activity Ledger", 8768, "/"),
    ("Crypto Storefront", 8772, "/"),
    ("Revenue Pipeline", 8773, "/api/status"),
    ("Sales & Marketing", 8774, "/api/status"),
    ("Customer CRM", 8775, "/api/status"),
    ("Commercial Operations", 8776, "/api/status"),
    ("Enterprise Automation", 8777, "/api/status"),
    ("Executive Intelligence", 8778, "/api/status"),
    ("Autonomous Operations", 8779, "/api/status"),
]

def check(name, port, path):
    url = f"http://127.0.0.1:{port}{path}"
    started = time.time()
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            raw = response.read()
            status = "online"
            try:
                payload = json.loads(raw.decode("utf-8"))
                status = payload.get("status") or status
            except Exception:
                pass
            return {
                "name": name, "port": port, "url": f"http://127.0.0.1:{port}",
                "alive": True, "status": status,
                "latency_ms": round((time.time() - started) * 1000, 1),
            }
    except Exception as exc:
        return {
            "name": name, "port": port, "url": f"http://127.0.0.1:{port}",
            "alive": False, "status": "offline", "error": str(exc),
            "latency_ms": round((time.time() - started) * 1000, 1),
        }

def snapshot():
    services = [check(*item) for item in SERVICES]
    alive = sum(1 for item in services if item["alive"])
    return {
        "status": "global_executive_dashboard_ready",
        "services_alive": alive,
        "services_total": len(services),
        "health_percent": round(alive / len(services) * 100),
        "alerts": [f"{item['name']} is offline" for item in services if not item["alive"]],
        "services": services,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

def page():
    state = snapshot()
    cards = []
    for item in state["services"]:
        cls = "ok" if item["alive"] else "bad"
        cards.append(
            f'<a class="service {cls}" href="{item["url"]}">'
            f'<h3>{item["name"]}</h3><p>{item["status"]}</p>'
            f'<small>Port {item["port"]} | {item["latency_ms"]} ms</small></a>'
        )
    alerts = "".join(f"<li>{a}</li>" for a in state["alerts"]) or "<li>No active service alerts.</li>"
    return f"""<!doctype html><html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>CompanyOS Global Executive Dashboard</title>
    <style>
    body{{margin:0;background:#09101f;color:#eef2ff;font-family:system-ui}}
    main{{max-width:1100px;margin:auto;padding:28px 20px}}
    .hero,.panel,.service{{background:#151d33;border-radius:20px;padding:22px;margin-bottom:18px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}}
    .service{{display:block;text-decoration:none;color:inherit;border:1px solid #273555}}
    .ok{{box-shadow:inset 4px 0 #4ade80}} .bad{{box-shadow:inset 4px 0 #fb7185}}
    h1{{font-size:clamp(36px,8vw,64px);line-height:1.05}}
    .metric{{font-size:28px;font-weight:700}} small{{color:#aab5d0}}
    </style></head><body><main>
    <h1>CompanyOS Global Executive Dashboard</h1>
    <section class="hero"><div class="metric">Health: {state["health_percent"]}%</div>
    <p>{state["services_alive"]} of {state["services_total"]} tracked services online</p>
    <p>Status: {state["status"]}</p></section>
    <section class="panel"><h2>System alerts</h2><ul>{alerts}</ul></section>
    <section><h2>CompanyOS modules</h2><div class="grid">{''.join(cards)}</div></section>
    </main></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/status":
            body = json.dumps(snapshot(), indent=2).encode()
            code, content_type = 200, "application/json"
        elif path in ("/", "/index.html"):
            body = page().encode()
            code, content_type = 200, "text/html; charset=utf-8"
        else:
            body = b'{"error":"not_found"}'
            code, content_type = 404, "application/json"
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

def main():
    print(f"CompanyOS Global Executive Dashboard V18 started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
