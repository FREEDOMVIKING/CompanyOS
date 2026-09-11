
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from .engine import AutonomousLaunchDirectorV36

HOST, PORT = "127.0.0.1", 8798
ENGINE = AutonomousLaunchDirectorV36(Path.home() / "companyos")

def page():
    s = ENGINE.run_cycle()
    cards = "".join(
        f"""<article>
        <h2>{v.get('name')}</h2>
        <p>Launch score: {v.get('launch_score')} / 100</p>
        <p>State: {v.get('launch_state')}</p>
        <p>Campaigns detected: {v.get('campaigns_detected')}</p>
        <p>Verified revenue: ${v.get('verified_revenue_usd')}</p>
        <p>Operations health: {v.get('operations_health_percent')}%</p>
        <p>Blockers: {', '.join(v.get('blockers', [])) or 'None'}</p>
        <p>{v.get('recommendation')}</p>
        </article>"""
        for v in s.get("ventures", [])
    )
    return f"""<!doctype html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CompanyOS Autonomous Launch Director</title>
<style>
body{{font-family:system-ui;background:#08101f;color:#eef2ff;margin:0}}
main{{max-width:1100px;margin:auto;padding:30px 20px}}
.hero,article{{background:#151d33;padding:22px;border-radius:18px;margin-bottom:18px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}}
.big{{font-size:36px;font-weight:800}}
</style></head><body><main>
<h1>CompanyOS Autonomous Launch Director</h1>
<section class="hero">
<p>Status: {s.get('status')}</p>
<p class="big">Ventures Evaluated: {s.get('ventures_evaluated')}</p>
<p>Ready for launch review: {s.get('ready_for_launch_review')}</p>
<p>Near ready: {s.get('near_ready')}</p>
<p>Review queue: {s.get('review_queue_size')}</p>
<p>Top launch candidate: {s.get('top_launch_candidate')}</p>
<p>Top launch score: {s.get('top_launch_score')}</p>
<p>Automatic external launch: {s.get('automatic_external_launch_enabled')}</p>
<p>Automatic publication: {s.get('automatic_publication_enabled')}</p>
</section>
<h2>Launch Pipeline</h2>
<section class="grid">{cards or '<article><p>No ventures available.</p></article>'}</section>
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
        state = None
        if p == "/api/status":
            self.send_json(ENGINE.run_cycle()); return
        if p == "/api/ventures":
            state = ENGINE.run_cycle()
            self.send_json({"ventures": state.get("ventures", [])}); return
        if p == "/api/reviews":
            state = ENGINE.run_cycle()
            self.send_json({"reviews": state.get("launch_review_queue", [])}); return
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
    print("CompanyOS Autonomous Launch Director V36 started: http://127.0.0.1:8798", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
