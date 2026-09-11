
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .engine import InternetOpportunityHunterV27

HOST, PORT = "127.0.0.1", 8789
ENGINE = InternetOpportunityHunterV27(Path.home() / "companyos")

def page():
    state = ENGINE.run_cycle()
    sources = "".join(
        f"<tr><td>{x.get('source_id')}</td><td>{x.get('status')}</td><td>{x.get('items')}</td></tr>"
        for x in state.get("source_status", [])
    )
    opportunities = "".join(
        f"""<article>
        <h2>{x.get('name')}</h2>
        <p>Confidence: {x.get('score')} / 100</p>
        <p>Status: {x.get('status')}</p>
        <p>{x.get('summary') or 'No summary provided.'}</p>
        <p>Keywords: {', '.join(x.get('keywords', []))}</p>
        </article>"""
        for x in state.get("opportunities", [])
    )
    return f"""<!doctype html><html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>CompanyOS Internet Opportunity Hunter</title>
    <style>
    body{{font-family:system-ui;background:#08101f;color:#eef2ff;margin:0}}
    main{{max-width:1100px;margin:auto;padding:30px 20px}}
    .hero,.panel,article{{background:#151d33;padding:22px;border-radius:18px;margin-bottom:18px}}
    table{{width:100%;border-collapse:collapse}} td,th{{padding:10px;border-bottom:1px solid #2a3553;text-align:left}}
    </style></head><body><main>
    <h1>CompanyOS Internet Opportunity Hunter</h1>
    <section class="hero">
      <p>Status: {state.get('status')}</p>
      <p>Network enabled: {state.get('network_enabled')}</p>
      <p>Sources OK: {state.get('sources_ok')} / {state.get('sources_total')}</p>
      <p>Signals collected: {state.get('signals_collected')}</p>
      <p>Opportunities discovered: {state.get('opportunities_discovered')}</p>
      <p>Top opportunity: {state.get('top_opportunity')}</p>
    </section>
    <section class="panel"><h2>Sources</h2>
      <table><tr><th>Source</th><th>Status</th><th>Items</th></tr>{sources}</table>
    </section>
    <h2>Discovery Queue</h2>
    {opportunities or '<article><p>No opportunities discovered yet.</p></article>'}
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
        if path == "/api/opportunities":
            self.send_json({"opportunities": ENGINE.run_cycle().get("opportunities", [])})
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
    print(f"CompanyOS Internet Opportunity Hunter V27 started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
