
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from .engine import CommandCenterV25

HOST, PORT = "127.0.0.1", 8787
ENGINE = CommandCenterV25(Path.home() / "companyos")

def page():
    state = ENGINE.snapshot()
    services = "".join(
        f"""<article class="{'ok' if s.get('alive') else 'bad'}">
        <h3>{s.get('name')}</h3>
        <p>{s.get('status')}</p>
        <p>Port {s.get('port')} · {s.get('latency_ms')} ms</p>
        </article>"""
        for s in state.get("services", [])
    )
    timeline = "".join(
        f"""<li><strong>{x.get('event_type') or x.get('event')}</strong>
        <br><small>{x.get('ts')}</small></li>"""
        for x in state.get("timeline", [])[:20]
    ) or "<li>No events yet.</li>"

    p = state.get("portfolio", {})
    r = state.get("revenue", {})
    w = state.get("workforce", {})
    research = state.get("research", {})
    learning = state.get("learning", {})

    return f"""<!doctype html><html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>CompanyOS Command Center</title>
    <style>
    body{{font-family:system-ui;background:#08101f;color:#eef2ff;margin:0}}
    main{{max-width:1200px;margin:auto;padding:30px 20px}}
    .hero,.panel,article{{background:#151d33;padding:22px;border-radius:18px;margin-bottom:18px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}}
    .ok{{box-shadow:inset 4px 0 #4ade80}} .bad{{box-shadow:inset 4px 0 #fb7185}}
    .metric{{font-size:30px;font-weight:800}}
    a.button{{display:inline-block;padding:12px 16px;border-radius:12px;background:#eef2ff;color:#08101f;text-decoration:none;font-weight:700;margin-right:8px}}
    li{{margin-bottom:12px}}
    </style></head><body><main>
    <h1>CompanyOS Command Center</h1>
    <section class="hero">
      <div class="metric">Health: {state.get('health_percent')}%</div>
      <p>{state.get('services_alive')} of {state.get('services_total')} services online</p>
      <p>Status: {state.get('status')}</p>
      <a class="button" href="/api/status">Health Check</a>
      <a class="button" href="/api/backup">Create Backup</a>
    </section>

    <section class="grid">
      <article><h2>Portfolio</h2><p>Ventures: {p.get('ventures_prepared')}</p><p>Launch review: {p.get('ready_for_launch_review')}</p><p>Top: {p.get('top_venture')}</p></article>
      <article><h2>Revenue</h2><p>Orders: {r.get('orders_total')}</p><p>Paid: {r.get('paid_orders')}</p><p>Revenue: ${r.get('revenue_usd')}</p></article>
      <article><h2>Workforce</h2><p>Agents: {w.get('agents_total')}</p><p>Tasks: {w.get('tasks_completed')} / {w.get('tasks_total')}</p><p>Blocked: {w.get('tasks_blocked')}</p></article>
      <article><h2>Research & Learning</h2><p>Network: {research.get('network_enabled')}</p><p>Evidence: {research.get('evidence_items')}</p><p>Lessons: {learning.get('lessons_generated')}</p></article>
    </section>

    <h2>Services</h2><section class="grid">{services}</section>
    <section class="panel"><h2>Live Event Timeline</h2><ul>{timeline}</ul></section>
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
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/status":
            self.send_json(ENGINE.snapshot())
            return
        if path == "/api/backup":
            self.send_json({"status": "backup_created", "path": ENGINE.create_backup()})
            return
        if path == "/api/control":
            q = parse_qs(parsed.query)
            controller = q.get("controller", [None])[0]
            action = q.get("action", ["status"])[0]
            self.send_json(ENGINE.local_action(controller, action))
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
    ENGINE.snapshot()
    print(f"CompanyOS Command Center V25 started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
