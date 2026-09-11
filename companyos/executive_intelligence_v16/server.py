import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .engine import ExecutiveIntelligenceV16

HOST, PORT = "127.0.0.1", 8778
ENGINE = ExecutiveIntelligenceV16(Path.home() / "companyos")

def dashboard():
    s = ENGINE.run_cycle()
    h = s.get("company_health", {})
    return f"""<!doctype html><html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>CompanyOS Executive Intelligence</title>
    <style>
    body{{font-family:system-ui;background:#0b1020;color:#eef2ff;margin:0}}
    main{{max-width:1050px;margin:auto;padding:30px 20px}}
    .card{{background:#151d33;padding:20px;border-radius:18px;margin-bottom:18px}}
    pre{{white-space:pre-wrap;word-break:break-word}}
    </style></head><body><main>
    <h1>CompanyOS Executive Intelligence</h1>
    <div class="card">
      <p>Status: {s.get('status')}</p>
      <p>Company health: {h.get('score')} / 100 — {h.get('rating')}</p>
      <p>Top opportunity: {s.get('top_opportunity')}</p>
      <p>External actions enabled: {s.get('external_actions_enabled')}</p>
    </div>
    <div class="card"><h2>Modules</h2><pre>{json.dumps(s.get('modules'), indent=2)}</pre></div>
    <div class="card"><h2>Bottlenecks</h2><pre>{json.dumps(s.get('bottlenecks'), indent=2)}</pre></div>
    <div class="card"><h2>Recommendations</h2><pre>{json.dumps(s.get('recommendations'), indent=2)}</pre></div>
    <div class="card"><h2>Opportunities</h2><pre>{json.dumps(s.get('opportunities'), indent=2)}</pre></div>
    </main></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def send_json(self, obj, code=200):
        body = json.dumps(obj, indent=2, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/status":
            self.send_json(ENGINE.run_cycle())
            return
        if path == "/api/timeline":
            self.send_json({"events": ENGINE.timeline()})
            return
        if path in ("/", "/index.html"):
            body = dashboard().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_json({"error": "not_found"}, 404)

def main():
    ENGINE.run_cycle()
    print(f"CompanyOS Executive Intelligence V16 started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
