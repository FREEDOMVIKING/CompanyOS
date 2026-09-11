
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .engine import AutonomousResearchNetworkV22

HOST, PORT = "127.0.0.1", 8784
ENGINE = AutonomousResearchNetworkV22(Path.home() / "companyos")

def page():
    state = ENGINE.run_cycle()
    source_rows = "".join(
        f"<tr><td>{x.get('source_id')}</td><td>{x.get('status')}</td><td>{x.get('items')}</td></tr>"
        for x in state.get("source_status", [])
    )
    venture_cards = []
    for item in state.get("venture_evidence", {}).values():
        venture_cards.append(f"""
        <article>
          <h2>{item.get('name')}</h2>
          <p>External signal score: {item.get('external_signal_score')} / 100</p>
          <p>Matched evidence items: {item.get('matched_items')}</p>
          <p>Competitors found: {len(item.get('competitors', []))}</p>
          <p>Observed prices: {item.get('observed_prices_usd')}</p>
        </article>
        """)
    return f"""<!doctype html><html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>CompanyOS Autonomous Research Network</title>
    <style>
    body{{font-family:system-ui;background:#0b1020;color:#eef2ff;margin:0}}
    main{{max-width:1000px;margin:auto;padding:30px 20px}}
    .hero,article,.panel{{background:#151d33;padding:22px;border-radius:18px;margin-bottom:18px}}
    table{{width:100%;border-collapse:collapse}} td,th{{padding:10px;border-bottom:1px solid #2a3553;text-align:left}}
    code{{word-break:break-word}}
    </style></head><body><main>
    <h1>CompanyOS Autonomous Research Network</h1>
    <section class="hero">
      <p>Status: {state.get('status')}</p>
      <p>Network enabled: {state.get('network_enabled')}</p>
      <p>Sources OK: {state.get('sources_ok')} / {state.get('sources_total')}</p>
      <p>Evidence items: {state.get('evidence_items')}</p>
      <p>Ventures analyzed: {state.get('ventures_analyzed')}</p>
    </section>
    <section class="panel"><h2>Research sources</h2>
      <table><tr><th>Source</th><th>Status</th><th>Items</th></tr>{source_rows}</table>
    </section>
    {''.join(venture_cards) or '<article><h2>No ventures found</h2></article>'}
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
        if path == "/api/evidence":
            self.send_json(ENGINE.run_cycle().get("venture_evidence", {}))
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
    print(f"CompanyOS Autonomous Research Network V22 started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
