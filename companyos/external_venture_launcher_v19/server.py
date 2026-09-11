
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .engine import ExternalVentureLauncherV19

HOST, PORT = "127.0.0.1", 8781
ENGINE = ExternalVentureLauncherV19(Path.home() / "companyos")

def page():
    state = ENGINE.run_cycle()
    cards = []
    for venture in state.get("launch_queue", []):
        cards.append(f"""
        <article>
          <h2>{venture.get('name')}</h2>
          <p>Readiness: {venture.get('readiness_score')} / 100</p>
          <p>State: {venture.get('state')}</p>
          <p>Workspace: <code>{venture.get('workspace')}</code></p>
          <p>External publication: approval required</p>
        </article>
        """)
    return f"""<!doctype html><html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>CompanyOS External Venture Launcher</title>
    <style>
    body{{font-family:system-ui;background:#0b1020;color:#eef2ff;margin:0}}
    main{{max-width:1000px;margin:auto;padding:30px 20px}}
    .hero,article{{background:#151d33;padding:22px;border-radius:18px;margin-bottom:18px}}
    code{{word-break:break-word;color:#a9c4ff}}
    </style></head><body><main>
    <h1>CompanyOS External Venture Launcher</h1>
    <section class="hero">
      <p>Status: {state.get('status')}</p>
      <p>Ventures prepared: {state.get('ventures_prepared')}</p>
      <p>Ready for launch review: {state.get('ready_for_launch_review')}</p>
      <p>Top venture: {state.get('top_venture')}</p>
      <p>External launch enabled: {state.get('external_launch_enabled')}</p>
    </section>
    {''.join(cards)}
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
        if path == "/api/ventures":
            self.send_json({"ventures": ENGINE.run_cycle().get("launch_queue", [])})
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
    print(f"CompanyOS External Venture Launcher V19 started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
