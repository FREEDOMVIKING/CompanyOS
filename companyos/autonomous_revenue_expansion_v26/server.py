
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .engine import AutonomousRevenueExpansionV26

HOST, PORT = "127.0.0.1", 8788
ENGINE = AutonomousRevenueExpansionV26(Path.home() / "companyos")

def page():
    state = ENGINE.run_cycle()
    cards = "".join(
        f"""<article>
        <h2>{x.get('name')}</h2>
        <p>Portfolio score: {x.get('portfolio_score')} / 100</p>
        <p>Action: {x.get('recommended_action')}</p>
        <p>Recommended price: ${x.get('recommended_price_usd')}</p>
        <p>Readiness: {x.get('readiness_score')}</p>
        <p>External signal: {x.get('external_signal_score')}</p>
        <p>Gross margin: {x.get('gross_margin_percent')}%</p>
        </article>"""
        for x in state.get("portfolio", [])
    )
    approvals = "".join(
        f"""<li>{x.get('name')} — {x.get('type')} — {x.get('status')}</li>"""
        for x in state.get("approval_queue", [])
    ) or "<li>No approval items.</li>"
    return f"""<!doctype html><html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>CompanyOS Autonomous Revenue Expansion</title>
    <style>
    body{{font-family:system-ui;background:#08101f;color:#eef2ff;margin:0}}
    main{{max-width:1100px;margin:auto;padding:30px 20px}}
    .hero,.panel,article{{background:#151d33;padding:22px;border-radius:18px;margin-bottom:18px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}}
    </style></head><body><main>
    <h1>CompanyOS Autonomous Revenue Expansion</h1>
    <section class="hero">
      <p>Status: {state.get('status')}</p>
      <p>Ventures: {state.get('ventures_total')}</p>
      <p>Promoted: {state.get('ventures_promoted')}</p>
      <p>On hold: {state.get('ventures_on_hold')}</p>
      <p>Top venture: {state.get('top_venture')}</p>
      <p>Verified revenue: ${state.get('verified_revenue_usd')}</p>
      <p>Automatic fund allocation: {state.get('automatic_fund_allocation_enabled')}</p>
    </section>
    <h2>Portfolio</h2><section class="grid">{cards or '<article><p>No ventures found.</p></article>'}</section>
    <section class="panel"><h2>Executive Approval Queue</h2><ul>{approvals}</ul></section>
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
        if path == "/api/portfolio":
            self.send_json({"portfolio": ENGINE.run_cycle().get("portfolio", [])})
            return
        if path == "/api/approvals":
            self.send_json({"approvals": ENGINE.run_cycle().get("approval_queue", [])})
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
    print(f"CompanyOS Autonomous Revenue Expansion V26 started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
