
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from .engine import AutonomousMarketingAcquisitionV31

HOST, PORT = "127.0.0.1", 8793
ENGINE = AutonomousMarketingAcquisitionV31(Path.home() / "companyos")

def page():
    state = ENGINE.run_cycle()
    cards = "".join(
        f"""<article>
        <h2>{c.get('product_name')}</h2>
        <p>Campaign score: {c.get('analytics',{}).get('campaign_score')} / 100</p>
        <p>Visitors: {c.get('analytics',{}).get('visitors')}</p>
        <p>Leads: {c.get('analytics',{}).get('leads')}</p>
        <p>Orders: {c.get('analytics',{}).get('orders')}</p>
        <p>Lead conversion: {c.get('analytics',{}).get('lead_conversion_percent')}%</p>
        <p>Order conversion: {c.get('analytics',{}).get('order_conversion_percent')}%</p>
        <p>Headline: {c.get('draft_assets',{}).get('headline')}</p>
        <p>Publishing: {c.get('external_publish_status')}</p>
        </article>"""
        for c in state.get("campaigns", [])
    )
    return f"""<!doctype html><html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>CompanyOS Autonomous Marketing & Acquisition</title>
    <style>
    body{{font-family:system-ui;background:#08101f;color:#eef2ff;margin:0}}
    main{{max-width:1100px;margin:auto;padding:30px 20px}}
    .hero,article{{background:#151d33;padding:22px;border-radius:18px;margin-bottom:18px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:16px}}
    </style></head><body><main>
    <h1>CompanyOS Autonomous Marketing & Customer Acquisition</h1>
    <section class="hero">
      <p>Status: {state.get('status')}</p>
      <p>Campaigns: {state.get('campaigns_total')}</p>
      <p>Leads: {state.get('leads_total')}</p>
      <p>Qualified leads: {state.get('qualified_leads')}</p>
      <p>Automatic posting: {state.get('automatic_posting_enabled')}</p>
      <p>Automatic ad spend: {state.get('automatic_ad_spend_enabled')}</p>
      <p>Automatic email: {state.get('automatic_email_enabled')}</p>
    </section>
    <h2>Campaign Portfolio</h2>
    <section class="grid">{cards or '<article><p>No products available for campaigns.</p></article>'}</section>
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
        if path == "/api/campaigns":
            self.send_json({"campaigns": ENGINE.run_cycle().get("campaigns", [])}); return
        if path == "/api/leads":
            self.send_json({"leads": ENGINE.run_cycle().get("lead_handoff_queue", [])}); return
        if path in ("/", "/index.html"):
            body = page().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body); return
        self.send_json({"error": "not_found"}, 404)

def main():
    ENGINE.run_cycle()
    print(f"CompanyOS Autonomous Marketing & Customer Acquisition V31 started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
