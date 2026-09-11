
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from .engine import AutonomousVentureIncubatorV35

HOST, PORT = "127.0.0.1", 8797
ENGINE = AutonomousVentureIncubatorV35(Path.home() / "companyos")

def page():
    s = ENGINE.run_cycle()
    cards = "".join(
        f"""<article>
        <h2>{c.get('name')}</h2>
        <p>Category: {c.get('category')}</p>
        <p>Business model: {c.get('model')}</p>
        <p>Overall score: {c.get('overall_score')} / 100</p>
        <p>Demand: {c.get('validation_score')}</p>
        <p>Profitability: {c.get('profitability_score')}</p>
        <p>Execution readiness: {c.get('execution_readiness_score')}</p>
        <p>Stage: {c.get('incubator_stage')}</p>
        <p>External launch approved: {c.get('external_launch_approved')}</p>
        </article>"""
        for c in s.get("candidates", [])
    )
    return f"""<!doctype html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CompanyOS Autonomous Venture Incubator</title>
<style>
body{{font-family:system-ui;background:#08101f;color:#eef2ff;margin:0}}
main{{max-width:1100px;margin:auto;padding:30px 20px}}
.hero,article{{background:#151d33;padding:22px;border-radius:18px;margin-bottom:18px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:16px}}
.big{{font-size:36px;font-weight:800}}
</style></head><body><main>
<h1>CompanyOS Autonomous Venture Incubator</h1>
<section class="hero">
<p>Status: {s.get('status')}</p>
<p class="big">Candidates: {s.get('candidates_total')}</p>
<p>Priority incubations: {s.get('priority_incubations')}</p>
<p>Validation queue: {s.get('validation_queue')}</p>
<p>Portfolio handoffs: {s.get('portfolio_handoffs')}</p>
<p>Top candidate: {s.get('top_candidate')}</p>
<p>Top candidate score: {s.get('top_candidate_score')}</p>
<p>{s.get('diversification_recommendation')}</p>
<p>Automatic company formation: {s.get('automatic_company_formation_enabled')}</p>
<p>Automatic external launch: {s.get('automatic_external_launch_enabled')}</p>
</section>
<h2>Incubator Pipeline</h2>
<section class="grid">{cards}</section>
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
        if p == "/api/candidates":
            self.send_json({"candidates": ENGINE.run_cycle().get("candidates", [])}); return
        if p == "/api/handoffs":
            self.send_json({"handoffs": ENGINE.run_cycle().get("portfolio_handoff_queue", [])}); return
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
    print("CompanyOS Autonomous Venture Incubator V35 started: http://127.0.0.1:8797", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
