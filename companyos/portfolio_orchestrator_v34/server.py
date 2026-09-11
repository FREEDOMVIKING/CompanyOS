
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from .engine import PortfolioOrchestratorV34

HOST, PORT = "127.0.0.1", 8796
ENGINE = PortfolioOrchestratorV34(Path.home() / "companyos")

def page():
    s = ENGINE.run_cycle()
    cards = "".join(
        f"""<article>
        <h2>{v.get('name')}</h2>
        <p>Portfolio score: {v.get('portfolio_score')} / 100</p>
        <p>Action: {v.get('recommended_action')}</p>
        <p>Products: {v.get('product_count')}</p>
        <p>Verified revenue: ${v.get('verified_revenue_usd')}</p>
        <p>Campaign support: {v.get('campaign_support')}</p>
        <p>Launch review ready: {v.get('launch_review_ready')}</p>
        </article>"""
        for v in s.get("ventures", [])
    )
    c = s.get("concentration", {})
    return f"""<!doctype html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CompanyOS Portfolio Orchestrator</title>
<style>
body{{font-family:system-ui;background:#08101f;color:#eef2ff;margin:0}}
main{{max-width:1100px;margin:auto;padding:30px 20px}}
.hero,article{{background:#151d33;padding:22px;border-radius:18px;margin-bottom:18px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:16px}}
.big{{font-size:36px;font-weight:800}}
</style></head><body><main>
<h1>CompanyOS Portfolio Management & Multi-Venture Orchestrator</h1>
<section class="hero">
<p>Status: {s.get('status')}</p>
<p class="big">Ventures: {s.get('ventures_total')}</p>
<p>Top venture: {s.get('top_venture')}</p>
<p>Top venture score: {s.get('top_venture_score')}</p>
<p>Concentration risk: {c.get('concentration_risk')}</p>
<p>Automatic capital reallocation: {s.get('automatic_capital_reallocation_enabled')}</p>
<p>Automatic venture retirement: {s.get('automatic_venture_retirement_enabled')}</p>
</section>
<h2>Venture Portfolio</h2>
<section class="grid">{cards or '<article><p>No ventures discovered yet.</p></article>'}</section>
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
        p = urlparse(self.path).path
        if p == "/api/status":
            self.send_json(ENGINE.run_cycle()); return
        if p == "/api/ventures":
            self.send_json({"ventures": ENGINE.run_cycle().get("ventures", [])}); return
        if p == "/api/allocations":
            self.send_json({"allocations": ENGINE.run_cycle().get("allocation_recommendations", [])}); return
        if p in ("/", "/index.html"):
            body = page().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body); return
        self.send_json({"error": "not_found"}, 404)

def main():
    ENGINE.run_cycle()
    print("CompanyOS Portfolio Orchestrator V34 started: http://127.0.0.1:8796", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
