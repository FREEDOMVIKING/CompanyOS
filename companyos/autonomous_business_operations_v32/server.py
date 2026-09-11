
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from .engine import AutonomousBusinessOperationsV32

HOST, PORT = "127.0.0.1", 8794
ENGINE = AutonomousBusinessOperationsV32(Path.home() / "companyos")

def page():
    state = ENGINE.run_cycle()
    workflows = "".join(
        f"""<article>
        <h2>{w.get('name')}</h2>
        <p>Priority: {w.get('priority')}</p>
        <p>Status: {w.get('status')}</p>
        <p>Assigned agent: {w.get('assigned_agent')}</p>
        <p>Next action: {w.get('next_action')}</p>
        </article>"""
        for w in state.get("workflows", [])
    )
    health = "".join(
        f"""<tr>
        <td>{m.get('module')}</td>
        <td>{m.get('status')}</td>
        <td>{'OK' if m.get('healthy') else 'CHECK'}</td>
        </tr>"""
        for m in state.get("module_health", [])
    )
    return f"""<!doctype html><html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>CompanyOS Autonomous Business Operations</title>
    <style>
    body{{font-family:system-ui;background:#08101f;color:#eef2ff;margin:0}}
    main{{max-width:1100px;margin:auto;padding:30px 20px}}
    .hero,.panel,article{{background:#151d33;padding:22px;border-radius:18px;margin-bottom:18px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:16px}}
    table{{width:100%;border-collapse:collapse}}td,th{{padding:10px;border-bottom:1px solid #2a3553;text-align:left}}
    .big{{font-size:36px;font-weight:800}}
    </style></head><body><main>
    <h1>CompanyOS Autonomous Business Operations</h1>
    <section class="hero">
      <p>Status: {state.get('status')}</p>
      <p class="big">Operations Health: {state.get('operations_health_percent')}%</p>
      <p>Healthy modules: {state.get('modules_healthy')} / {state.get('modules_total')}</p>
      <p>Workflows: {state.get('workflow_count')}</p>
      <p>Queued internal tasks: {state.get('queued_internal_tasks')}</p>
      <p>Stalled workflows: {state.get('stalled_workflows')}</p>
      <p>Top priority: {state.get('top_priority_workflow')}</p>
      <p>Automatic external actions: {state.get('automatic_external_actions_enabled')}</p>
    </section>
    <section class="panel"><h2>Module Health</h2>
      <table><tr><th>Module</th><th>Status</th><th>Health</th></tr>{health}</table>
    </section>
    <h2>Workflow Graph</h2>
    <section class="grid">{workflows}</section>
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
        if path == "/api/workflows":
            self.send_json({"workflows": ENGINE.run_cycle().get("workflows", [])}); return
        if path == "/api/queue":
            self.send_json({"queue": ENGINE.run_cycle().get("execution_queue", [])}); return
        if path == "/api/recovery":
            self.send_json({"recovery_candidates": ENGINE.run_cycle().get("recovery_candidates", [])}); return
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
    print(f"CompanyOS Autonomous Business Operations V32 started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
