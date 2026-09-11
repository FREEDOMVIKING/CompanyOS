
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .engine import ValidationLaunchDirectorV20

HOST, PORT = "127.0.0.1", 8782
ENGINE = ValidationLaunchDirectorV20(Path.home() / "companyos")

def page():
    state = ENGINE.run_cycle()
    cards = []
    for item in state.get("results", []):
        cards.append(f"""
        <article>
          <h2>{item.get('name')}</h2>
          <p>Validation score: {item.get('validation_score')} / 100</p>
          <p>State: {item.get('state')}</p>
          <p>Recommended price: ${item.get('recommended_price_usd')}</p>
          <p>Recommendation: {item.get('launch_recommendation')}</p>
          <p>Blockers: {', '.join(item.get('blockers', [])) or 'None'}</p>
        </article>
        """)
    return f"""<!doctype html><html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>CompanyOS Validation & Launch Director</title>
    <style>
    body{{font-family:system-ui;background:#0b1020;color:#eef2ff;margin:0}}
    main{{max-width:1000px;margin:auto;padding:30px 20px}}
    .hero,article{{background:#151d33;padding:22px;border-radius:18px;margin-bottom:18px}}
    </style></head><body><main>
    <h1>CompanyOS Validation & Launch Director</h1>
    <section class="hero">
      <p>Status: {state.get('status')}</p>
      <p>Ventures validated: {state.get('ventures_validated')}</p>
      <p>Ready for launch review: {state.get('ready_for_launch_review')}</p>
      <p>Needs more validation: {state.get('needs_more_validation')}</p>
      <p>External launch enabled: {state.get('external_launch_enabled')}</p>
    </section>
    {''.join(cards) or '<article><h2>No ventures found</h2></article>'}
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
        if path == "/api/results":
            self.send_json({"results": ENGINE.run_cycle().get("results", [])})
            return
        if path in ("/", "/index.html"):
            body = page().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_json({"error": "not_found"}, 404)

def main():
    ENGINE.run_cycle()
    print(f"CompanyOS Validation & Launch Director V20 started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
