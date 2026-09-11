import json,threading,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse
from .core import UnifiedCoreV4

HOST,PORT="127.0.0.1",9000
CORE=UnifiedCoreV4(Path.home()/"companyos")

def esc(s):
    s="" if s is None else str(s)
    return (s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
             .replace('"',"&quot;").replace("'","&#39;"))

def nav():
    return """<nav><a href="/">Overview</a><a href="/ceo">CEO</a><a href="/goals">Goals</a>
    <a href="/ventures">Ventures</a><a href="/agents">Agents</a><a href="/tasks">Tasks</a>
    <a href="/memory">Memory</a><a href="/decisions">Decisions</a><a href="/plugins">Plugins</a>
    <a href="/modules">Modules</a><a href="/events">Events</a></nav>"""

def shell(title,body):
    return f"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><style>
body{{font-family:system-ui;background:#07101f;color:#eef2ff;margin:0}}main{{max-width:1200px;margin:auto;padding:24px}}
nav{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px}}nav a{{color:#dbe8ff;text-decoration:none;background:#17233a;padding:10px 12px;border-radius:10px}}
.card{{background:#151d33;padding:20px;border-radius:18px;margin:14px 0}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}}
.big{{font-size:40px;font-weight:800}}table{{width:100%;border-collapse:collapse}}td,th{{padding:9px;border-bottom:1px solid #2a3550;text-align:left}}
</style></head><body><main>{nav()}<h1>{esc(title)}</h1>{body}</main></body></html>"""

def table(title,headers,rows):
    h="".join(f"<th>{esc(x)}</th>" for x in headers)
    r="".join("<tr>"+"".join(f"<td>{esc(v)}</td>" for v in row)+"</tr>" for row in rows)
    return shell(title,f'<section class="card"><table><tr>{h}</tr>{r}</table></section>')

def overview():
    s=CORE.status()
    return shell("CompanyOS Unified Autonomous Core V4",f"""
    <section class="card"><div class="big">CEO Intelligence: ONLINE</div>
    <p>Status: {esc(s['status'])}</p><p>Health: {s['health_percent']}%</p><p>Ventures: {s['ventures_total']}</p>
    <p>Top venture: {esc(s['top_venture'])} ({s['top_venture_score']})</p><p>Agents: {s['agents_total']}</p>
    <p>Plugins: {s['plugins_total']}</p><p>Goals: {s['goals_total']}</p><p>Executive memories: {s['memories_total']}</p>
    <p>Latest executive decision: {esc(s['latest_executive_decision'])}</p></section>
    <section class="card"><h2>Autonomy layer</h2><p>Strategy engine: ON</p><p>Dynamic delegation: ON</p>
    <p>Critic/debate loop: ON</p><p>Executive memory: ON</p><p>Continuous planning: ON</p></section>
    <section class="card"><h2>External action gates</h2><p>Publication: False</p><p>Spending: False</p>
    <p>Wallet signing: False</p><p>Transfers: False</p><p>Customer outreach: False</p><p>Domain purchases: False</p></section>""")

class H(BaseHTTPRequestHandler):
    def send_body(self,b,code=200,ctype="text/html; charset=utf-8"):
        if isinstance(b,str): b=b.encode()
        self.send_response(code); self.send_header("Content-Type",ctype); self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(b))); self.end_headers()
        try:self.wfile.write(b)
        except BrokenPipeError:pass
    def send_json(self,o,code=200): self.send_body(json.dumps(o,indent=2,default=str),code,"application/json")
    def do_GET(self):
        p=urlparse(self.path).path
        if p=="/api/status": return self.send_json(CORE.status())
        if p=="/api/cycle": return self.send_json(CORE.run_cycle())
        if p=="/api/migrate": return self.send_json(CORE.migrate())
        if p=="/": return self.send_body(overview())
        if p=="/ceo":
            d=CORE.db.list_decisions(10)
            body='<section class="card"><h2>Executive Decisions</h2>'+''.join(f'<p><b>{esc(x["subject"])}</b>: {esc(x["decision"])} — {esc(x["rationale"])}</p>' for x in d)+'</section>'
            return self.send_body(shell("CEO",body))
        if p=="/goals":
            return self.send_body(table("Goals",["Goal","Status","Priority"],[(x["title"],x["status"],x["priority"]) for x in CORE.db.list_goals()]))
        if p=="/ventures":
            return self.send_body(table("Ventures",["Name","Stage","Score"],[(x["name"],x.get("stage"),x.get("score")) for x in CORE.db.list_ventures()]))
        if p=="/agents":
            return self.send_body(table("Agents",["Name","Role","Completed","Failed"],[(x["name"],x["role"],x["completed"],x["failed"]) for x in CORE.db.list_agents()]))
        if p=="/tasks":
            return self.send_body(table("Tasks",["Task","Agent","Status","Priority"],[(x["title"],x["agent"],x["status"],x["priority"]) for x in CORE.db.list_tasks(200)]))
        if p=="/memory":
            return self.send_body(table("Memory",["Type","Subject","Importance"],[(x["memory_type"],x["subject"],x["importance"]) for x in CORE.db.list_memories(100)]))
        if p=="/decisions":
            return self.send_body(table("Decisions",["Subject","Decision","Confidence"],[(x["subject"],x["decision"],x["confidence"]) for x in CORE.db.list_decisions(100)]))
        if p=="/plugins":
            return self.send_body(table("Plugins",["Name","Version","Health"],[(x["name"],x["version"],x["health"]) for x in CORE.db.list_plugins()]))
        if p=="/modules":
            return self.send_body(table("Modules",["Module","Status","Healthy"],[(x["name"],x["status"],bool(x["healthy"])) for x in CORE.db.list_modules()]))
        if p=="/events":
            return self.send_body(table("Events",["Time","Type","Source","Target"],[(x["created_at"],x["event_type"],x["source"],x.get("target")) for x in CORE.db.list_events(200)]))
        return self.send_json({"error":"not_found"},404)

def loop():
    while True:
        time.sleep(20)
        try: CORE.run_cycle()
        except Exception as e: CORE.db.event("runtime.error","server",{"error":str(e)})

def main():
    CORE.run_cycle()
    threading.Thread(target=loop,daemon=True,name="companyos-v4-loop").start()
    print("CompanyOS Unified Autonomous Core V4 started: http://127.0.0.1:9000",flush=True)
    ThreadingHTTPServer((HOST,PORT),H).serve_forever()

if __name__=="__main__": main()
