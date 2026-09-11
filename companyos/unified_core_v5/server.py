import json, threading, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from .core import UnifiedCoreV5

HOST,PORT="127.0.0.1",9000
CORE=UnifiedCoreV5(Path.home()/"companyos")

def esc(s):
    s="" if s is None else str(s)
    return (s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
             .replace('"',"&quot;").replace("'","&#39;"))

def nav():
    return """<nav><a href="/">Overview</a><a href="/ceo">CEO</a><a href="/companies">Companies</a>
    <a href="/ventures">Ventures</a><a href="/goals">Goals</a><a href="/agents">Agents</a>
    <a href="/tasks">Tasks</a><a href="/kpis">KPIs</a><a href="/forecast">Forecast</a>
    <a href="/plugins">Plugins</a><a href="/memory">Memory</a><a href="/events">Events</a>
    <a href="/health">Health</a></nav>"""

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
    return shell("CompanyOS Unified Autonomous Core V5",f"""
    <section class="card"><div class="big">Final Foundation: ONLINE</div>
    <p>Status: {esc(s['status'])}</p><p>Health: {s['health_percent']}%</p>
    <p>Companies: {s['companies_total']}</p><p>Ventures: {s['ventures_total']}</p>
    <p>Top venture: {esc(s['top_venture'])} ({s['top_venture_score']})</p>
    <p>Agents: {s['agents_total']}</p><p>Plugins: {s['plugins_total']}</p>
    <p>Goals: {s['goals_total']}</p><p>Latest CEO decision: {esc(s['latest_executive_decision'])}</p></section>
    <section class="card"><h2>Architecture</h2><p>Plugin-first upgrades: ON</p><p>Hot plugin discovery: ON</p>
    <p>Executive planning: ON</p><p>KPI engine: ON</p><p>Forecast engine: ON</p>
    <p>Portfolio engine: ON</p><p>Agent performance scoring: ON</p><p>Internal retries/recovery: ON</p></section>
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
        if p=="/api/reload-plugins": return self.send_json(CORE.reload_plugins())
        if p=="/": return self.send_body(overview())
        if p=="/ceo":
            ds=CORE.db.list_decisions(20)
            return self.send_body(table("CEO Decisions",["Subject","Decision","Confidence"],[(d["subject"],d["decision"],d["confidence"]) for d in ds]))
        if p=="/companies":
            return self.send_body(table("Companies",["Name","Status","Ventures","Revenue"],[(x["name"],x["status"],x["venture_count"],x["revenue_usd"]) for x in CORE.db.list_companies()]))
        if p=="/ventures":
            return self.send_body(table("Ventures",["Name","Stage","Score"],[(x["name"],x.get("stage"),x.get("score")) for x in CORE.db.list_ventures()]))
        if p=="/goals":
            return self.send_body(table("Goals",["Goal","Status","Priority"],[(x["title"],x["status"],x["priority"]) for x in CORE.db.list_goals()]))
        if p=="/agents":
            return self.send_body(table("Agents",["Name","Role","Completed","Failed","Score"],[(x["name"],x["role"],x["completed"],x["failed"],x["score"]) for x in CORE.db.list_agents()]))
        if p=="/tasks":
            return self.send_body(table("Tasks",["Task","Agent","Plugin","Status"],[(x["title"],x["agent"],x.get("plugin_id"),x["status"]) for x in CORE.db.list_tasks(250)]))
        if p=="/kpis":
            k=CORE.db.get_kv("kpis",{}) or {}
            return self.send_body(table("KPIs",["Metric","Value"],list(k.items())))
        if p=="/forecast":
            f=CORE.db.get_kv("revenue_forecast",{}) or {}
            return self.send_body(table("Forecast",["Field","Value"],list(f.items())))
        if p=="/plugins":
            return self.send_body(table("Plugins",["Name","Version","Health","Enabled"],[(x["name"],x["version"],x["health"],bool(x["enabled"])) for x in CORE.db.list_plugins()]))
        if p=="/memory":
            return self.send_body(table("Memory",["Type","Subject","Importance"],[(x["memory_type"],x["subject"],x["importance"]) for x in CORE.db.list_memories(120)]))
        if p=="/events":
            return self.send_body(table("Events",["Time","Type","Source","Target"],[(x["created_at"],x["event_type"],x["source"],x.get("target")) for x in CORE.db.list_events(250)]))
        if p=="/health":
            h=CORE.recovery.health()
            return self.send_body(table("Health",["Field","Value"],list(h.items())))
        return self.send_json({"error":"not_found"},404)

def loop():
    while True:
        time.sleep(20)
        try: CORE.run_cycle()
        except Exception as e: CORE.db.event("runtime.error","server",{"error":str(e)})

def main():
    CORE.run_cycle()
    threading.Thread(target=loop,daemon=True,name="companyos-v5-loop").start()
    print("CompanyOS Unified Autonomous Core V5 started: http://127.0.0.1:9000",flush=True)
    ThreadingHTTPServer((HOST,PORT),H).serve_forever()

if __name__=="__main__":
    main()
