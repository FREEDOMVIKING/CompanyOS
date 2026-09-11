
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .engine import AutonomousSpecialistWorkforceV24

HOST, PORT = "127.0.0.1", 8786
ENGINE = AutonomousSpecialistWorkforceV24(Path.home() / "companyos")

def page():
    state = ENGINE.run_cycle()
    agents = "".join(
        f"""<article>
        <h2>{item.get('agent')}</h2>
        <p>Assigned: {item.get('assigned')}</p>
        <p>Completed: {item.get('completed')}</p>
        <p>Completion rate: {item.get('completion_rate')}</p>
        </article>"""
        for item in state.get("agent_performance", {}).values()
    )
    tasks = "".join(
        f"""<article>
        <h2>{task.get('title')}</h2>
        <p>Agent: {task.get('assigned_role')}</p>
        <p>Priority: {task.get('priority')}</p>
        <p>Status: {task.get('status')}</p>
        </article>"""
        for task in state.get("tasks", [])
    )
    return f"""<!doctype html><html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>CompanyOS Autonomous Specialist Workforce</title>
    <style>
    body{{font-family:system-ui;background:#0b1020;color:#eef2ff;margin:0}}
    main{{max-width:1100px;margin:auto;padding:30px 20px}}
    .hero,article{{background:#151d33;padding:22px;border-radius:18px;margin-bottom:18px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}}
    </style></head><body><main>
    <h1>CompanyOS Autonomous Specialist Workforce</h1>
    <section class="hero">
      <p>Status: {state.get('status')}</p>
      <p>Agents: {state.get('agents_total')}</p>
      <p>Tasks completed: {state.get('tasks_completed')} / {state.get('tasks_total')}</p>
      <p>Tasks blocked: {state.get('tasks_blocked')}</p>
      <p>Automatic external actions: {state.get('automatic_external_actions_enabled')}</p>
    </section>
    <h2>Agent Performance</h2><section class="grid">{agents}</section>
    <h2>Task Queue</h2><section class="grid">{tasks}</section>
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
        if path == "/api/tasks":
            self.send_json({"tasks": ENGINE.run_cycle().get("tasks", [])})
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
    print(f"CompanyOS Autonomous Specialist Workforce V24 started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
