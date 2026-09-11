import json, threading, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from .core import UnifiedCoreV3

HOST,PORT="127.0.0.1",9000
CORE=UnifiedCoreV3(Path.home()/"companyos")

def esc(s):
    s="" if s is None else str(s)
    return (s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
             .replace('"',"&quot;").replace("'","&#39;"))

def nav():
    return """<nav><a href="/">Overview</a><a href="/ventures">Ventures</a><a href="/agents">Agents</a>
    <a href="/tasks">Tasks</a><a href="/modules">Modules</a><a href="/plugins">Plugins</a>
    <a href="/events">Events</a><a href="/health">Health</a></nav>"""

def shell(title,body):
    return f"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><style>
body{{font-family:system-ui;background:#07101f;color:#eef2ff;margin:0}}main{{max-width:1200px;margin:auto;padding:24px}}
nav{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px}}nav a{{color:#dbe8ff;text-decoration:none;background:#17233a;padding:10px 12px;border-radius:10px}}
.card{{background:#151d33;padding:20px;border-radius:18px;margin:14px 0}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}}
.big{{font-size:40px;font-weight:800}}table{{width:100%;border-collapse:collapse}}td,th{{padding:9px;border-bottom:1px solid #2a3550;text-align:left}}
</style></head><body><main>{nav()}<h1>{esc(title)}</h1>{body}</main></body></html>"""

def overview():
    s=CORE.status()
    return shell("CompanyOS Unified Autonomous Core V3",f"""
    <section class="card"><div class="big">Health: {s['health_percent']}%</div>
    <p>Status: {esc(s['status'])}</p><p>Modules: {s['modules_total']}</p><p>Ventures: {s['ventures_total']}</p>
    <p>Top venture: {esc(s['top_venture'])} ({s['top_venture_score']})</p><p>Agents: {s['agents_total']}</p>
    <p>Plugins: {s['plugins_total']}</p><p>Tasks: queued {s['tasks']['queued']} · running {s['tasks']['running']} · completed {s['tasks']['completed']} · failed {s['tasks']['failed']} · dead {s['tasks']['dead']}</p></section>
    <section class="card"><h2>V3 runtime upgrades</h2><p>Persistent event bus: ON</p><p>Persistent scheduler: ON</p>
    <p>Plugin registry: ON</p><p>Self-healing monitor: ON</p><p>Automatic local retries: ON</p></section>
    <section class="card"><h2>External action gates</h2><p>Publication: False</p><p>Spending: False</p>
    <p>Wallet signing: False</p><p>Fund transfers: False</p><p>Customer outreach: False</p><p>Domain purchases: False</p></section>""")

def table_page(title, headers, rows):
    h="".join(f"<th>{esc(x)}</th>" for x in headers)
    r="".join("<tr>"+"".join(f"<td>{esc(v)}</td>" for v in row)+"</tr>" for row in rows)
    return shell(title,f'<section class="card"><table><tr>{h}</tr>{r}</table></section>')

class H(BaseHTTPRequestHandler):
    def send_body(self,b,code=200,ctype="text/html; charset=utf-8"):
        if isinstance(b,str): b=b.encode()
        self.send_response(code);self.send_header("Content-Type",ctype);self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(b)));self.end_headers()
        try:self.wfile.write(b)
        except BrokenPipeError:pass
    def send_json(self,o,code=200): self.send_body(json.dumps(o,indent=2,default=str),code,"application/json")
    def do_GET(self):
        p=urlparse(self.path).path
        if p=="/api/status": return self.send_json(CORE.status())
        if p=="/api/cycle": return self.send_json(CORE.run_cycle())
        if p=="/api/migrate": return self.send_json(CORE.migrate())
        if p=="/": return self.send_body(overview())
        if p=="/ventures":
            return self.send_body(table_page("Ventures",["Name","Stage","Score"],[(x["name"],x.get("stage"),x.get("score")) for x in CORE.db.list_ventures()]))
        if p=="/agents":
            return self.send_body(table_page("Agents",["Name","Role","Completed","Failed"],[(x["name"],x["role"],x["completed"],x["failed"]) for x in CORE.db.list_agents()]))
        if p=="/tasks":
            return self.send_body(table_page("Tasks",["Task","Agent","Status","Priority"],[(x["title"],x["agent"],x["status"],x["priority"]) for x in CORE.db.list_tasks(200)]))
        if p=="/modules":
            return self.send_body(table_page("Modules",["Module","Status","Healthy"],[(x["name"],x["status"],bool(x["healthy"])) for x in CORE.db.list_modules()]))
        if p=="/plugins":
            return self.send_body(table_page("Plugins",["Plugin","Version","Health","Enabled"],[(x["name"],x["version"],x["health"],bool(x["enabled"])) for x in CORE.db.list_plugins()]))
        if p=="/events":
            return self.send_body(table_page("Events",["Time","Type","Source","Target"],[(x["created_at"],x["event_type"],x["source"],x.get("target")) for x in CORE.db.list_events(200)]))
        if p=="/health":
            r=CORE.health.inspect()
            return self.send_body(shell("Health",f'<section class="card"><div class="big">{r["health_percent"]}%</div><p>Unhealthy modules: {r["unhealthy_modules"]}</p><p>Unhealthy plugins: {r["unhealthy_plugins"]}</p><p>Recommendations: {esc("; ".join(r["recommendations"]) or "None")}</p></section>'))
        return self.send_json({"error":"not_found"},404)

def loop():
    while True:
        time.sleep(15)
        try: CORE.run_cycle()
        except Exception as e: CORE.bus.publish("runtime.error","server",{"error":str(e)})

def main():
    CORE.run_cycle()
    threading.Thread(target=loop,daemon=True,name="companyos-v3-loop").start()
    print("CompanyOS Unified Autonomous Core V3 started: http://127.0.0.1:9000",flush=True)
    ThreadingHTTPServer((HOST,PORT),H).serve_forever()

if __name__=="__main__": main()
