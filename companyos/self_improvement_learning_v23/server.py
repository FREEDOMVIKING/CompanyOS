
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .engine import SelfImprovementLearningV23

HOST, PORT = "127.0.0.1", 8785
ENGINE = SelfImprovementLearningV23(Path.home() / "companyos")

def page():
    state = ENGINE.run_cycle()
    proposals = "".join(
        f"""<article>
        <h2>{x.get('title')}</h2>
        <p>Priority: {x.get('priority')}</p>
        <p>Type: {x.get('change_type')}</p>
        <p>{x.get('description')}</p>
        <p>Status: {x.get('status')}</p>
        </article>"""
        for x in state.get("improvement_proposals", [])
    )
    pricing = "".join(
        f"""<article>
        <h2>{x.get('name')}</h2>
        <p>Recommended price: ${x.get('recommended_price_usd')}</p>
        <p>Confidence: {x.get('confidence')}</p>
        <p>Real sales validation required: {x.get('requires_real_sales_validation')}</p>
        </article>"""
        for x in state.get("pricing_recommendations", [])
    )
    return f"""<!doctype html><html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>CompanyOS Self-Improvement & Learning</title>
    <style>
    body{{font-family:system-ui;background:#0b1020;color:#eef2ff;margin:0}}
    main{{max-width:1000px;margin:auto;padding:30px 20px}}
    .hero,article{{background:#151d33;padding:22px;border-radius:18px;margin-bottom:18px}}
    </style></head><body><main>
    <h1>CompanyOS Self-Improvement & Learning</h1>
    <section class="hero">
      <p>Status: {state.get('status')}</p>
      <p>Lessons generated: {state.get('lessons_generated')}</p>
      <p>Knowledge categories: {state.get('knowledge_categories')}</p>
      <p>Automatic code changes enabled: {state.get('automatic_code_changes_enabled')}</p>
      <p>External actions enabled: {state.get('external_actions_enabled')}</p>
    </section>
    <h2>Improvement Proposals</h2>
    {proposals or '<article><p>No proposals yet.</p></article>'}
    <h2>Pricing Recommendations</h2>
    {pricing or '<article><p>No pricing recommendations yet.</p></article>'}
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
        if path == "/api/proposals":
            self.send_json({"proposals": ENGINE.run_cycle().get("improvement_proposals", [])})
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
    print(f"CompanyOS Self-Improvement & Learning V23 started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
