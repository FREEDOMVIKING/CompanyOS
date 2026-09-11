import json, threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from .core import UnifiedCore

HOST, PORT = "127.0.0.1", 9000
CORE = UnifiedCore(Path.home() / "companyos")

def esc(s):
    s = "" if s is None else str(s)
    return (s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
             .replace('"',"&quot;").replace("'","&#39;"))

def nav():
    return """<nav>
    <a href="/">Overview</a>
    <a href="/ventures">Ventures</a>
    <a href="/agents">Agents</a>
    <a href="/tasks">Tasks</a>
    <a href="/modules">Modules</a>
    <a href="/events">Events</a>
    </nav>"""

def shell(title, body):
    return f"""<!doctype html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<style>
body{{font-family:system-ui;background:#07101f;color:#eef2ff;margin:0}}
main{{max-width:1200px;margin:auto;padding:24px}}
nav{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}}
nav a{{color:#cfe1ff;text-decoration:none;background:#17233a;padding:10px 12px;border-radius:10px}}
.card{{background:#151d33;padding:20px;border-radius:18px;margin:14px 0}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}}
.big{{font-size:40px;font-weight:800}}
.small{{opacity:.78;font-size:14px}}
table{{width:100%;border-collapse:collapse}} td,th{{padding:10px;text-align:left;border-bottom:1px solid #2a3550}}
.good{{color:#8ff0b8}} .bad{{color:#ffb0b0}}
</style></head><body><main>{nav()}<h1>{esc(title)}</h1>{body}</main></body></html>"""

def overview():
    s = CORE.status()
    return shell("CompanyOS Unified Autonomous Core V2", f"""
    <section class="card">
      <div class="big">Health: {s['health_percent']}%</div>
      <p>Status: {esc(s['status'])}</p>
      <p>Modules: {s['modules_healthy']} healthy / {s['modules_total']} tracked</p>
      <p>Ventures: {s['ventures_total']}</p>
      <p>Top venture: {esc(s['top_venture'])} ({s['top_venture_score']})</p>
      <p>Agents: {s['agents_total']}</p>
      <p>Tasks: queued {s['tasks']['queued']} · running {s['tasks']['running']} · completed {s['tasks']['completed']} · failed {s['tasks']['failed']}</p>
    </section>
    <section class="card">
      <h2>External action gates</h2>
      <p>Publication: False</p><p>Spending: False</p><p>Wallet signing: False</p>
      <p>Fund transfers: False</p><p>Customer outreach: False</p><p>Domain purchases: False</p>
    </section>
    """)

def ventures_page():
    rows = CORE.db.list_ventures()
    body = '<div class="grid">' + ''.join(
        f'<section class="card"><h2>{esc(v["name"])}</h2><p>Score: {v["score"]}</p><p>Stage: {esc(v["stage"])}</p><p class="small">Source: {esc(v["source"])}</p></section>'
        for v in rows
    ) + '</div>'
    return shell("Ventures", body or '<section class="card">No ventures imported yet.</section>')

def agents_page():
    rows = CORE.db.list_agents()
    body = '<div class="grid">' + ''.join(
        f'<section class="card"><h2>{esc(a["name"])}</h2><p>{esc(a["role"])}</p><p>Completed: {a["completed"]} · Failed: {a["failed"]}</p></section>'
        for a in rows
    ) + '</div>'
    return shell("Agents", body)

def tasks_page():
    rows = CORE.db.list_tasks(100)
    body = '<section class="card"><table><tr><th>Task</th><th>Agent</th><th>Status</th><th>Priority</th></tr>' + ''.join(
        f'<tr><td>{esc(t["title"])}</td><td>{esc(t["agent"])}</td><td>{esc(t["status"])}</td><td>{t["priority"]}</td></tr>'
        for t in rows
    ) + '</table></section>'
    return shell("Tasks", body)

def modules_page():
    rows = CORE.db.list_modules()
    body = '<section class="card"><table><tr><th>Module</th><th>Status</th><th>Healthy</th></tr>' + ''.join(
        f'<tr><td>{esc(m["name"])}</td><td>{esc(m["status"])}</td><td>{"YES" if m["healthy"] else "NO"}</td></tr>'
        for m in rows
    ) + '</table></section>'
    return shell("Modules", body)

def events_page():
    rows = CORE.db.list_events(100)
    body = '<section class="card"><table><tr><th>Time</th><th>Type</th><th>Source</th></tr>' + ''.join(
        f'<tr><td>{esc(e["created_at"])}</td><td>{esc(e["event_type"])}</td><td>{esc(e["source"])}</td></tr>'
        for e in rows
    ) + '</table></section>'
    return shell("Events", body)

class Handler(BaseHTTPRequestHandler):
    def send_body(self, body, code=200, ctype="text/html; charset=utf-8"):
        if isinstance(body, str): body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try: self.wfile.write(body)
        except BrokenPipeError: pass

    def send_json(self, obj, code=200):
        self.send_body(json.dumps(obj, indent=2, default=str), code, "application/json")

    def do_GET(self):
        p = urlparse(self.path).path
        if p == "/api/status": return self.send_json(CORE.status())
        if p == "/api/ventures": return self.send_json({"ventures":CORE.db.list_ventures()})
        if p == "/api/agents": return self.send_json({"agents":CORE.db.list_agents()})
        if p == "/api/tasks": return self.send_json({"tasks":CORE.db.list_tasks(200)})
        if p == "/api/modules": return self.send_json({"modules":CORE.db.list_modules()})
        if p == "/api/events": return self.send_json({"events":CORE.db.list_events(200)})
        if p == "/api/migrate": return self.send_json(CORE.migrate())
        if p == "/api/cycle": return self.send_json(CORE.run_cycle())
        if p == "/": return self.send_body(overview())
        if p == "/ventures": return self.send_body(ventures_page())
        if p == "/agents": return self.send_body(agents_page())
        if p == "/tasks": return self.send_body(tasks_page())
        if p == "/modules": return self.send_body(modules_page())
        if p == "/events": return self.send_body(events_page())
        return self.send_json({"error":"not_found"},404)

def main():
    CORE.run_cycle()
    CORE.orchestrator.start()
    print("CompanyOS Unified Autonomous Core V2 started: http://127.0.0.1:9000", flush=True)
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()

if __name__ == "__main__":
    main()
