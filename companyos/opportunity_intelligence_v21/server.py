
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .engine import OpportunityIntelligenceV21

HOST, PORT = "127.0.0.1", 8783
ENGINE = OpportunityIntelligenceV21(Path.home() / "companyos")

def page():
    state = ENGINE.run_cycle()
    cards = []
    for item in state.get("results", []):
        s = item["scores"]
        cards.append(f"""
        <article>
          <h2>{item.get('name')}</h2>
          <p>Overall score: {s.get('overall')} / 100</p>
          <p>Demand evidence: {s.get('demand_evidence')} / 35</p>
          <p>Offer quality: {s.get('offer_quality')} / 25</p>
          <p>Profitability: {s.get('profitability')} / 20</p>
          <p>Execution readiness: {s.get('execution_readiness')} / 20</p>
          <p>Confidence: {item.get('confidence')}</p>
          <p>External research: {item.get('external_research_status')}</p>
        </article>
        """)
    return f"""<!doctype html><html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>CompanyOS Opportunity Intelligence</title>
    <style>
    body{{font-family:system-ui;background:#0b1020;color:#eef2ff;margin:0}}
    main{{max-width:1000px;margin:auto;padding:30px 20px}}
    .hero,article{{background:#151d33;padding:22px;border-radius:18px;margin-bottom:18px}}
    </style></head><body><main>
    <h1>CompanyOS Opportunity Intelligence</h1>
    <section class="hero">
      <p>Status: {state.get('status')}</p>
      <p>Opportunities scored: {state.get('opportunities_scored')}</p>
      <p>Strong internal evidence: {state.get('strong_internal_evidence')}</p>
      <p>Top opportunity: {state.get('top_opportunity')}</p>
      <p>External research provider connected: {state.get('external_research_provider_connected')}</p>
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
    print(f"CompanyOS Opportunity Intelligence V21 started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
