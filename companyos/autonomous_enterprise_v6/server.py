import json, threading, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from .core import EnterpriseCoreV6

HOST,PORT="127.0.0.1",9000
CORE=EnterpriseCoreV6(Path.home()/"companyos")

def esc(s):
    s="" if s is None else str(s)
    return (s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
             .replace('"',"&quot;").replace("'","&#39;"))

def nav():
    return """<nav><a href="/">Overview</a><a href="/companies">Companies</a>
    <a href="/ceos">Company CEOs</a><a href="/agents">Agents</a><a href="/tasks">Tasks</a>
    <a href="/decisions">Decisions</a><a href="/kpis">KPIs</a><a href="/events">Activity</a>
    <a href="/recovery">Recovery</a></nav>"""

def shell(title,body):
    return f"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><style>
body{{font-family:system-ui;background:#07101f;color:#eef2ff;margin:0}}
main{{max-width:1200px;margin:auto;padding:24px}}
nav{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px}}
nav a{{color:#dbe8ff;text-decoration:none;background:#17233a;padding:10px 12px;border-radius:10px}}
.card{{background:#151d33;padding:20px;border-radius:18px;margin:14px 0}}
.big{{font-size:40px;font-weight:800}}
table{{width:100%;border-collapse:collapse}}td,th{{padding:9px;border-bottom:1px solid #2a3550;text-align:left}}
</style></head><body><main>{nav()}<h1>{esc(title)}</h1>{body}</main></body></html>"""

def table(title,headers,rows):
    h="".join(f"<th>{esc(x)}</th>" for x in headers)
    r="".join("<tr>"+"".join(f"<td>{esc(v)}</td>" for v in row)+"</tr>" for row in rows)
    return shell(title,f'<section class="card"><table><tr>{h}</tr>{r}</table></section>')

def overview():
    s=CORE.status()
    p=s["provider"]
    return shell("CompanyOS Autonomous Enterprise V6",f"""
    <section class="card"><div class="big">Enterprise Orchestration: ONLINE</div>
    <p>Status: {esc(s['status'])}</p>
    <p>Companies: {s['companies_total']}</p>
    <p>Top company: {esc(s['top_company'])} ({s['top_company_priority']})</p>
    <p>Agents: {s['agents_total']}</p>
    <p>Executive decisions: {s['decisions_total']}</p>
    <p>AI mode: {esc(p['mode'])}</p>
    <p>Provider: {esc(p['provider'])}</p>
    <p>Local fallback: {p['local_fallback_enabled']}</p></section>
    <section class="card"><h2>Enterprise capabilities</h2>
    <p>Per-company CEOs: ON</p><p>Dynamic specialist teams: ON</p>
    <p>Cross-company routing: ON</p><p>Enterprise KPI aggregation: ON</p>
    <p>Recovery advisor: ON</p><p>Provider abstraction: ON</p></section>
    <section class="card"><h2>External action gates</h2>
    <p>Publication: False</p><p>Domain purchases: False</p><p>Spending: False</p>
    <p>Wallet signing: False</p><p>Transfers: False</p><p>Customer outreach: False</p></section>
    """)

class H(BaseHTTPRequestHandler):
    def send_body(self,b,code=200,ctype="text/html; charset=utf-8"):
        if isinstance(b,str): b=b.encode()
        self.send_response(code); self.send_header("Content-Type",ctype); self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(b))); self.end_headers()
        try:self.wfile.write(b)
        except BrokenPipeError:pass

    def send_json(self,o,code=200):
        self.send_body(json.dumps(o,indent=2,default=str),code,"application/json")

    def do_GET(self):
        p=urlparse(self.path).path
        if p=="/api/status": return self.send_json(CORE.status())
        if p=="/api/cycle": return self.send_json(CORE.run_cycle())
        if p=="/api/migrate": return self.send_json(CORE.migrate())
        if p=="/": return self.send_body(overview())
        if p=="/companies":
            return self.send_body(table("Companies",["Name","Status","Priority"],[(x["name"],x["status"],x["priority"]) for x in CORE.db.list_companies()]))
        if p=="/ceos":
            rows=[x for x in CORE.db.list_agents() if x["role"]=="company_ceo"]
            return self.send_body(table("Company CEOs",["Name","Score","Completed","Failed"],[(x["name"],x["score"],x["completed"],x["failed"]) for x in rows]))
        if p=="/agents":
            return self.send_body(table("Agents",["Name","Role","Score","Completed","Failed"],[(x["name"],x["role"],x["score"],x["completed"],x["failed"]) for x in CORE.db.list_agents()]))
        if p=="/tasks":
            return self.send_body(table("Tasks",["Task","Company","Agent","Status"],[(x["title"],x.get("company_id"),x.get("agent_id"),x["status"]) for x in CORE.db.list_tasks(300)]))
        if p=="/decisions":
            return self.send_body(table("Decisions",["Subject","Decision","Confidence"],[(x["subject"],x["decision"],x["confidence"]) for x in CORE.db.list_decisions(200)]))
        if p=="/kpis":
            k=CORE.db.get_kv("enterprise_kpis",{}) or {}
            return self.send_body(table("Enterprise KPIs",["Metric","Value"],list(k.items())))
        if p=="/events":
            return self.send_body(table("Activity",["Time","Type","Source","Target"],[(x["created_at"],x["event_type"],x["source"],x.get("target")) for x in CORE.db.list_events(300)]))
        if p=="/recovery":
            r=CORE.recovery.inspect()
            return self.send_body(table("Recovery",["Field","Value"],list(r.items())))
        return self.send_json({"error":"not_found"},404)

def loop():
    while True:
        time.sleep(20)
        try: CORE.run_cycle()
        except Exception as e: CORE.db.event("runtime.error","server",{"error":str(e)})

def main():
    CORE.run_cycle()
    threading.Thread(target=loop,daemon=True,name="companyos-enterprise-v6-loop").start()
    print("CompanyOS Autonomous Enterprise V6 started: http://127.0.0.1:9000",flush=True)
    ThreadingHTTPServer((HOST,PORT),H).serve_forever()

if __name__=="__main__":
    main()
