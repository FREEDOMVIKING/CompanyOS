import json, threading, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse
from .core import EnterpriseOSV8

CORE=EnterpriseOSV8(Path.home()/"companyos")
def e(x):
    x="" if x is None else str(x)
    return x.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def nav():
    return """<nav><a href="/">Overview</a><a href="/strategy">Strategy</a><a href="/companies">Companies</a>
<a href="/agents">Agents</a><a href="/forecast">Forecast</a><a href="/improvements">Improvements</a>
<a href="/sandbox">Sandbox</a><a href="/budget">Budget</a><a href="/activity">Activity</a></nav>"""

def page(title,body):
    return f"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><style>
body{{font-family:system-ui;background:#07101f;color:#eef2ff;margin:0}}main{{max-width:1200px;margin:auto;padding:24px}}
nav{{display:flex;gap:10px;flex-wrap:wrap}}nav a{{color:#dbe8ff;text-decoration:none;background:#17233a;padding:10px 12px;border-radius:10px}}
.card{{background:#151d33;padding:20px;border-radius:18px;margin:16px 0}}.big{{font-size:40px;font-weight:800}}
table{{width:100%;border-collapse:collapse}}td,th{{padding:9px;border-bottom:1px solid #2a3550;text-align:left}}
</style></head><body><main>{nav()}<h1>{e(title)}</h1>{body}</main></body></html>"""

def table(title,heads,rows):
    return page(title,'<div class="card"><table><tr>'+''.join(f'<th>{e(h)}</th>' for h in heads)+'</tr>'+
                ''.join('<tr>'+''.join(f'<td>{e(v)}</td>' for v in r)+'</tr>' for r in rows)+'</table></div>')

class H(BaseHTTPRequestHandler):
    def out(self,b,ctype="text/html; charset=utf-8"):
        if isinstance(b,str):b=b.encode()
        self.send_response(200);self.send_header("Content-Type",ctype);self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def do_GET(self):
        p=urlparse(self.path).path
        if p=="/api/status": return self.out(json.dumps(CORE.status(),indent=2),"application/json")
        if p=="/api/cycle": return self.out(json.dumps(CORE.cycle(),indent=2),"application/json")
        if p=="/":
            s=CORE.status()
            return self.out(page("CompanyOS Autonomous Enterprise OS V8",f"""<div class="card"><div class="big">Enterprise OS: ONLINE</div>
<p>Status: {e(s['status'])}</p><p>Companies: {s['companies_total']}</p><p>Agents: {s['agents_total']}</p>
<p>Average company health: {s['average_company_health']}%</p><p>Strategic goals: {s['strategic_goals_total']}</p>
<p>Forecasts: {s['forecasts_total']}</p><p>Improvement proposals: {s['improvement_proposals_total']}</p>
<p>Sandbox validated: {s['sandbox_validated_total']}</p><p>Budget plans: {s['budget_plans_total']}</p></div>
<div class="card"><h2>Self-improvement</h2><p>Analysis: ON</p><p>Proposal generation: ON</p>
<p>Sandbox validation: ON</p><p>Automatic live code replacement: False</p></div>"""))
        if p=="/strategy": return self.out(table("Strategy",["Days","Goal","Priority","Status"],[(x["horizon"],x["title"],x["priority"],x["status"]) for x in CORE.q("SELECT * FROM goals ORDER BY horizon")]))
        if p=="/companies": return self.out(table("Companies",["Name","Status","Priority","Health"],[(x["name"],x["status"],x["priority"],x["health"]) for x in CORE.q("SELECT * FROM companies ORDER BY priority DESC")]))
        if p=="/agents": return self.out(table("Agents",["Name","Role","Score","Completed","Failed"],[(x["name"],x["role"],x["score"],x["completed"],x["failed"]) for x in CORE.q("SELECT * FROM agents ORDER BY score DESC")]))
        if p=="/forecast": return self.out(table("Forecast",["Days","Metric","Value","Confidence"],[(x["horizon"],x["metric"],x["value"],x["confidence"]) for x in CORE.q("SELECT * FROM forecasts ORDER BY horizon")]))
        if p=="/improvements": return self.out(table("Improvements",["Type","Subject","Priority","Risk","Status"],[(x["kind"],x["subject"],x["priority"],x["risk"],x["status"]) for x in CORE.q("SELECT * FROM proposals ORDER BY priority DESC")]))
        if p=="/sandbox": return self.out(table("Sandbox",["Proposal","Status","Score"],[(x["proposal_id"],x["status"],x["score"]) for x in CORE.q("SELECT * FROM sandbox ORDER BY updated_at DESC")]))
        if p=="/budget": return self.out(table("Budget",["Company","Amount","Status"],[(x["company_id"],x["amount"],x["status"]) for x in CORE.q("SELECT * FROM budgets ORDER BY amount DESC")]))
        if p=="/activity": return self.out(table("Activity",["Time","Type","Source"],[(x["created_at"],x["type"],x["source"]) for x in CORE.q("SELECT * FROM events ORDER BY id DESC LIMIT 300")]))
        return self.out('{"error":"not_found"}',"application/json")

def loop():
    while True:
        time.sleep(20)
        try:CORE.cycle()
        except Exception as ex:CORE.event("runtime.error","server",{"error":str(ex)})

def main():
    CORE.cycle()
    threading.Thread(target=loop,daemon=True).start()
    print("CompanyOS Enterprise OS V8 started: http://127.0.0.1:9000",flush=True)
    ThreadingHTTPServer(("127.0.0.1",9000),H).serve_forever()
if __name__=="__main__":main()
