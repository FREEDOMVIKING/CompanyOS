import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .engine import EnterpriseAutomationV15

HOST, PORT = "127.0.0.1", 8777
ENGINE = EnterpriseAutomationV15(Path.home() / "companyos")

def dashboard():
    s = ENGINE.run_cycle()
    return f"""<!doctype html><html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>CompanyOS Enterprise Automation</title>
    <style>
    body{{font-family:system-ui;background:#0b1020;color:#eef2ff;margin:0}}
    main{{max-width:1000px;margin:auto;padding:30px 20px}}
    .card{{background:#151d33;padding:20px;border-radius:18px;margin-bottom:18px}}
    pre{{white-space:pre-wrap;word-break:break-word}}
    </style></head><body><main>
    <h1>CompanyOS Enterprise Automation</h1>
    <div class="card">
      <p>Status: {s.get('status')}</p>
      <p>Top priority: {s.get('top_priority_venture')}</p>
      <p>External commitments enabled: {s.get('external_commitments_enabled')}</p>
    </div>
    <div class="card"><h2>Portfolio KPIs</h2><pre>{json.dumps(s.get('kpis'), indent=2)}</pre></div>
    <div class="card"><h2>Cash-Flow Forecast</h2><pre>{json.dumps(s.get('cashflow_forecast'), indent=2)}</pre></div>
    <div class="card"><h2>Hiring Plan</h2><pre>{json.dumps(s.get('hiring_plan'), indent=2)}</pre></div>
    <div class="card"><h2>Venture Priorities</h2><pre>{json.dumps(s.get('venture_priorities'), indent=2)}</pre></div>
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
            self.send_json(ENGINE.run_cycle()); return
        if path == "/api/intelligence":
            state = ENGINE.run_cycle()
            self.send_json(state.get("daily_intelligence", {})); return
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
    print(f"CompanyOS Enterprise Automation V15 started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
