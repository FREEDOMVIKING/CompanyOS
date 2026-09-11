import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .engine import CommercialOperationsV14

HOST, PORT = "127.0.0.1", 8776
ENGINE = CommercialOperationsV14(Path.home() / "companyos")

def dashboard():
    s = ENGINE.run_cycle()
    return f"""<!doctype html><html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>CompanyOS Commercial Operations</title>
    <style>
    body{{font-family:system-ui;background:#0b1020;color:#eef2ff;margin:0}}
    main{{max-width:1000px;margin:auto;padding:30px 20px}}
    .card{{background:#151d33;padding:20px;border-radius:18px;margin-bottom:18px}}
    </style></head><body><main>
    <h1>CompanyOS Commercial Operations</h1>
    <div class="card">
      <p>Status: {s.get('status')}</p>
      <p>Support drafts: {s.get('support_drafts')}</p>
      <p>A/B tests planned: {s.get('ab_tests_planned')}</p>
      <p>Draft-only mode: {s.get('draft_only_mode')}</p>
    </div>
    <div class="card"><h2>Sales Funnel</h2><pre>{json.dumps(s.get('funnel'), indent=2)}</pre></div>
    <div class="card"><h2>Portfolio</h2><pre>{json.dumps(s.get('portfolio'), indent=2)}</pre></div>
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

    def read_payload(self):
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/status":
            self.send_json(ENGINE.run_cycle()); return
        if path == "/api/ab-tests":
            self.send_json({"tests": ENGINE.ab_tests()}); return
        if path in ("/", "/index.html"):
            body = dashboard().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_json({"error": "not_found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            payload = self.read_payload()
            if path == "/api/quotes":
                self.send_json({"ok": True, "quote": ENGINE.create_quote(payload)}, 201); return
            if path == "/api/proposals":
                self.send_json({"ok": True, "proposal": ENGINE.create_proposal(payload)}, 201); return
            if path == "/api/contracts":
                self.send_json({"ok": True, "contract": ENGINE.create_contract(payload)}, 201); return
            if path == "/api/invoices":
                self.send_json({"ok": True, "invoice": ENGINE.create_invoice(payload)}, 201); return
            self.send_json({"error": "not_found"}, 404)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, 400)

def main():
    ENGINE.run_cycle()
    print(f"CompanyOS Commercial Operations V14 started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
