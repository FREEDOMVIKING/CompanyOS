import json, threading, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from .core import EnterpriseExpansionV9

CORE=EnterpriseExpansionV9(Path.home()/"companyos")

def esc(s):
    s="" if s is None else str(s)
    return (s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
             .replace('"',"&quot;").replace("'","&#39;"))

def nav():
    return """<nav><a href="/">Overview</a><a href="/companies">Companies</a><a href="/agents">Agents</a>
    <a href="/memory">Memory</a><a href="/opportunities">Opportunities</a>
    <a href="/capital">Capital</a><a href="/reassignments">Reassignments</a>
    <a href="/recovery">Recovery</a><a href="/tasks">Tasks</a><a href="/activity">Activity</a></nav>"""

def page(title,body):
    return f"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="15"><title>{esc(title)}</title><style>
body{{font-family:system-ui;background:#07101f;color:#eef2ff;margin:0}}main{{max-width:1200px;margin:auto;padding:24px}}
nav{{display:flex;gap:10px;flex-wrap:wrap}}nav a{{color:#dbe8ff;text-decoration:none;background:#17233a;padding:10px 12px;border-radius:10px}}
.card{{background:#151d33;padding:20px;border-radius:18px;margin:16px 0}}.big{{font-size:40px;font-weight:800}}
table{{width:100%;border-collapse:collapse}}td,th{{padding:9px;border-bottom:1px solid #2a3550;text-align:left}}
</style></head><body><main>{nav()}<h1>{esc(title)}</h1>{body}</main></body></html>"""

def table(title,heads,rows):
    return page(title,'<div class="card"><table><tr>'+''.join(f'<th>{esc(h)}</th>' for h in heads)+'</tr>'+
                ''.join('<tr>'+''.join(f'<td>{esc(v)}</td>' for v in r)+'</tr>' for r in rows)+'</table></div>')

def overview():
    s=CORE.status()
    return page("CompanyOS Autonomous Enterprise Expansion V9",f"""
    <div class="card"><div class="big">Enterprise Expansion: ONLINE</div>
    <p>Status: {esc(s['status'])}</p>
    <p>Companies: {s['companies_total']}</p>
    <p>Agents: {s['agents_total']}</p>
    <p>Average company health: {s['average_company_health']}%</p>
    <p>Top company: {esc(s['top_company'])} ({s['top_company_priority']})</p>
    <p>Executive memories: {s['executive_memories_total']}</p>
    <p>Opportunities: {s['opportunities_total']}</p>
    <p>High-priority opportunities: {s['high_priority_opportunities']}</p>
    <p>Capital plans: {s['capital_plans_total']}</p>
    <p>Reassignment plans: {s['reassignment_plans_total']}</p>
    <p>Recovery actions: {s['recovery_actions_total']}</p></div>
    <div class="card"><h2>Autonomy</h2>
    <p>Internal planning: ON</p><p>Internal delegation: ON</p>
    <p>Internal team rebalancing proposals: ON</p><p>Opportunity scoring: ON</p>
    <p>Pre-cycle snapshots: ON</p></div>
    <div class="card"><h2>External action gates</h2>
    <p>Publication: False</p><p>Domains: False</p><p>Accounts: False</p>
    <p>Spending: False</p><p>Wallet signing: False</p><p>Transfers: False</p>
    <p>Customer outreach: False</p><p>Automatic live-code replacement: False</p></div>""")

class H(BaseHTTPRequestHandler):
    def out(self,b,ctype="text/html; charset=utf-8"):
        if isinstance(b,str): b=b.encode()
        self.send_response(200)
        self.send_header("Content-Type",ctype)
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(b)))
        self.end_headers()
        try:self.wfile.write(b)
        except BrokenPipeError:pass

    def do_GET(self):
        p=urlparse(self.path).path
        if p=="/api/status": return self.out(json.dumps(CORE.status(),indent=2),"application/json")
        if p=="/api/cycle": return self.out(json.dumps(CORE.cycle(),indent=2),"application/json")
        if p=="/api/migrate": return self.out(json.dumps(CORE.migrate(),indent=2),"application/json")
        if p=="/": return self.out(overview())
        if p=="/companies":
            return self.out(table("Companies",["Name","Status","Priority","Health"],[(x["name"],x["status"],x["priority"],x["health"]) for x in CORE.db.list_companies()]))
        if p=="/agents":
            return self.out(table("Agents",["Name","Role","Company","Score"],[(x["name"],x["role"],x.get("company_id"),x["score"]) for x in CORE.db.list_agents()]))
        if p=="/memory":
            return self.out(table("Executive Memory",["Type","Subject","Company","Importance"],[(x["memory_type"],x["subject"],x.get("company_id"),x["importance"]) for x in CORE.db.list_memories(500)]))
        if p=="/opportunities":
            return self.out(table("Opportunities",["Name","Category","Score","Status"],[(x["name"],x["category"],x["score"],x["status"]) for x in CORE.db.list_opportunities()]))
        if p=="/capital":
            return self.out(table("Capital Planning",["Company","Amount","Priority","Status"],[(x["company_id"],x["amount_usd"],x["priority"],x["status"]) for x in CORE.db.list_allocations()]))
        if p=="/reassignments":
            return self.out(table("Agent Reassignment Plans",["Agent","From","To","Status"],[(x["agent_id"],x["from_company_id"],x["to_company_id"],x["status"]) for x in CORE.db.list_reassignments()]))
        if p=="/recovery":
            return self.out(table("Recovery",["Company","Action","Priority","Status"],[(x["company_id"],x["action_type"],x["priority"],x["status"]) for x in CORE.db.list_recovery()]))
        if p=="/tasks":
            return self.out(table("Tasks",["Task","Company","Status","Priority"],[(x["title"],x.get("company_id"),x["status"],x["priority"]) for x in CORE.db.list_tasks(500)]))
        if p=="/activity":
            return self.out(table("Activity",["Time","Type","Source","Target"],[(x["created_at"],x["event_type"],x["source"],x.get("target")) for x in CORE.db.list_events(500)]))
        return self.out('{"error":"not_found"}',"application/json")

def loop():
    while True:
        time.sleep(20)
        try:CORE.cycle()
        except Exception as ex:CORE.db.event("runtime.error","server",{"error":str(ex)})

def main():
    CORE.cycle()
    threading.Thread(target=loop,daemon=True).start()
    print("CompanyOS Enterprise Expansion V9 started: http://127.0.0.1:9000",flush=True)
    ThreadingHTTPServer(("127.0.0.1",9000),H).serve_forever()

if __name__=="__main__":
    main()
