import json, threading, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from .core import EnterpriseNetworkV7

CORE = EnterpriseNetworkV7(Path.home()/"companyos")

def esc(x):
    return str(x if x is not None else "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def nav():
    links=[("/","Overview"),("/global-ceo","Global CEO"),("/companies","Companies"),("/opportunities","Opportunities"),
           ("/collaboration","Collaboration"),("/resources","Resources"),("/agents","Agents"),("/tasks","Tasks"),
           ("/memory","Shared Memory"),("/activity","Activity")]
    return "<nav>"+"".join(f'<a href="{p}">{n}</a>' for p,n in links)+"</nav>"

def shell(title,body):
    return f'''<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{{font-family:system-ui;background:#07101f;color:#eef2ff;margin:0}}
main{{max-width:1200px;margin:auto;padding:24px}}
nav{{display:flex;gap:10px;flex-wrap:wrap}}
a{{color:#dbe8ff;text-decoration:none;background:#17233a;padding:10px 12px;border-radius:10px}}
.card{{background:#151d33;padding:20px;border-radius:18px;margin:14px 0}}
.big{{font-size:40px;font-weight:800}}
table{{width:100%;border-collapse:collapse}} td,th{{padding:9px;border-bottom:1px solid #2a3550;text-align:left}}
</style><main>{nav()}<h1>{esc(title)}</h1>{body}</main>'''

def table(title,headers,rows):
    h="".join(f"<th>{esc(x)}</th>" for x in headers)
    r="".join("<tr>"+"".join(f"<td>{esc(v)}</td>" for v in row)+"</tr>" for row in rows)
    return shell(title,f'<div class="card"><table><tr>{h}</tr>{r}</table></div>')

def overview():
    s=CORE.status()
    return shell("CompanyOS Autonomous Enterprise Network V7",f'''
    <div class="card"><div class="big">Enterprise Network: ONLINE</div>
    <p>Status: {esc(s["status"])}</p><p>Companies: {s["companies_total"]}</p>
    <p>Average company health: {s["average_company_health"]}%</p>
    <p>Top company: {esc(s["top_company"])} ({s["top_company_priority"]})</p>
    <p>Agents: {s["agents_total"]}</p><p>Opportunities: {s["opportunities_total"]}</p>
    <p>Company proposals ready: {s["company_proposals_ready"]}</p>
    <p>Collaborations: {s["collaborations_total"]}</p>
    <p>Resource allocations: {s["resource_allocations_total"]}</p>
    <p>Shared memories: {s["shared_memories_total"]}</p></div>
    <div class="card"><h2>External action gates</h2>
    <p>Company formation: False</p><p>Publication: False</p><p>Domains: False</p>
    <p>Spending: False</p><p>Wallet signing: False</p><p>Transfers: False</p><p>Customer outreach: False</p></div>''')

class H(BaseHTTPRequestHandler):
    def out(self,b,ctype="text/html; charset=utf-8"):
        if isinstance(b,str): b=b.encode()
        self.send_response(200); self.send_header("Content-Type",ctype); self.send_header("Content-Length",str(len(b))); self.end_headers()
        try: self.wfile.write(b)
        except BrokenPipeError: pass

    def do_GET(self):
        p=urlparse(self.path).path
        if p=="/api/status": return self.out(json.dumps(CORE.status(),indent=2),"application/json")
        if p=="/api/cycle": return self.out(json.dumps(CORE.run_cycle(),indent=2),"application/json")
        if p=="/": return self.out(overview())
        if p=="/global-ceo": return self.out(table("Global CEO",["Subject","Decision","Confidence"],[(d["subject"],d["decision"],d["confidence"]) for d in CORE.decisions()]))
        if p=="/companies": return self.out(table("Companies",["Name","Status","Priority","Health"],[(c["name"],c["status"],c["priority"],c["health"]) for c in CORE.companies()]))
        if p=="/opportunities": return self.out(table("Opportunities",["Name","Category","Score","Status"],[(o["name"],o["category"],o["score"],o["status"]) for o in CORE.opportunities()]))
        if p=="/collaboration": return self.out(table("Collaboration",["Source","Target","Score","Status"],[(x["source_id"],x["target_id"],x["score"],x["status"]) for x in CORE.collaborations()]))
        if p=="/resources": return self.out(table("Resources",["Agent","From","To","Status"],[(x["agent_id"],x["from_id"],x["to_id"],x["status"]) for x in CORE.allocations()]))
        if p=="/agents": return self.out(table("Agents",["Name","Role","Company","Score"],[(a["name"],a["role"],a["company_id"],a["score"]) for a in CORE.agents()]))
        if p=="/tasks": return self.out(table("Tasks",["Task","Company","Status","Priority"],[(t["title"],t["company_id"],t["status"],t["priority"]) for t in CORE.tasks()]))
        if p=="/memory": return self.out(table("Shared Memory",["Type","Subject","Importance"],[(m["kind"],m["subject"],m["importance"]) for m in CORE.memories()]))
        if p=="/activity": return self.out(table("Activity",["Time","Type","Source","Target"],[(e["created_at"],e["type"],e["source"],e["target"]) for e in CORE.events()]))
        return self.out(json.dumps({"error":"not_found"}),"application/json")

def loop():
    while True:
        time.sleep(20)
        try: CORE.run_cycle()
        except Exception: pass

def main():
    CORE.run_cycle()
    threading.Thread(target=loop,daemon=True).start()
    print("CompanyOS Enterprise Network V7 started: http://127.0.0.1:9000",flush=True)
    ThreadingHTTPServer(("127.0.0.1",9000),H).serve_forever()

if __name__=="__main__": main()
