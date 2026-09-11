import json, threading, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse
from .core import AutonomousCompanyBuilderV13

CORE=AutonomousCompanyBuilderV13(Path.home()/"companyos")

def esc(s):
    s="" if s is None else str(s)
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def nav():
    return """<nav><a href="/">Overview</a><a href="/queue">Launch Queue</a><a href="/builds">Company Builds</a>
<a href="/products">Products</a><a href="/campaigns">Marketing</a><a href="/sales">Sales</a>
<a href="/lifecycle">Lifecycle</a><a href="/reinvestment">Reinvestment</a><a href="/activity">Activity</a></nav>"""

def page(title,body):
    return f"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="20"><title>{esc(title)}</title><style>
body{{font-family:system-ui;background:#07101f;color:#eef2ff;margin:0}}main{{max-width:1200px;margin:auto;padding:24px}}
nav{{display:flex;gap:10px;flex-wrap:wrap}}nav a{{color:#dbe8ff;text-decoration:none;background:#17233a;padding:10px 12px;border-radius:10px}}
.card{{background:#151d33;padding:20px;border-radius:18px;margin:16px 0}}.big{{font-size:42px;font-weight:800}}
table{{width:100%;border-collapse:collapse}}td,th{{padding:9px;border-bottom:1px solid #2a3550;text-align:left}}
</style></head><body><main>{nav()}<h1>{esc(title)}</h1>{body}</main></body></html>"""

def table(title,heads,rows):
    return page(title,'<div class="card"><table><tr>'+''.join(f'<th>{esc(h)}</th>' for h in heads)+'</tr>'+
                ''.join('<tr>'+''.join(f'<td>{esc(v)}</td>' for v in r)+'</tr>' for r in rows)+'</table></div>')

class H(BaseHTTPRequestHandler):
    def out(self,b,ctype="text/html; charset=utf-8"):
        if isinstance(b,str):b=b.encode()
        self.send_response(200); self.send_header("Content-Type",ctype); self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(b))); self.end_headers()
        try:self.wfile.write(b)
        except BrokenPipeError:pass

    def do_GET(self):
        p=urlparse(self.path).path
        if p=="/api/status": return self.out(json.dumps(CORE.status(),indent=2),"application/json")
        if p=="/api/cycle": return self.out(json.dumps(CORE.cycle(),indent=2),"application/json")
        if p=="/":
            s=CORE.status()
            return self.out(page("CompanyOS Autonomous Company Builder V13",f"""
<div class="card"><div class="big">Company Builder: ONLINE</div>
<p>Status: {esc(s['status'])}</p><p>Companies imported: {s['legacy_companies_total']}</p><p>Agents: {s['agents_total']}</p>
<p>Venture handoffs: {s['venture_handoffs_total']}</p><p>Launch queue: {s['launch_queue_total']}</p>
<p>Local company builds: {s['local_company_builds_total']}</p><p>Products: {s['products_total']}</p>
<p>Marketing campaigns: {s['marketing_campaigns_total']}</p><p>Sales plans: {s['sales_plans_total']}</p>
<p>Verified revenue: ${s['verified_revenue']}</p><p>Reinvestment recommendations: {s['reinvestment_recommendations_total']}</p></div>
<div class="card"><h2>External execution gates</h2>
<p>External publish: False</p><p>Domain purchase: False</p><p>Account creation: False</p>
<p>Spending: False</p><p>Fund transfers: False</p></div>"""))
        maps={
            "/queue":("Launch Queue",["Company","Status","Priority","Board Score","Recommendation"],
                      [(x["company_name"],x["status"],x["priority"],x["board_score"],x["recommendation"]) for x in CORE.db.rows("SELECT * FROM launch_queue ORDER BY priority DESC")]),
            "/builds":("Company Builds",["Company","Status","Workspace","Website"],
                       [(x["company_name"],x["status"],x["workspace_path"],x["website_path"]) for x in CORE.db.rows("SELECT * FROM company_builds ORDER BY updated_at DESC")]),
            "/products":("Products",["Name","Type","Status","Price Hint"],
                         [(x["name"],x["product_type"],x["status"],x["price_hint"]) for x in CORE.db.rows("SELECT * FROM products ORDER BY updated_at DESC")]),
            "/campaigns":("Marketing Campaigns",["Name","Channel","Status","Message"],
                          [(x["name"],x["channel"],x["status"],x["message"]) for x in CORE.db.rows("SELECT * FROM campaigns ORDER BY updated_at DESC")]),
            "/sales":("Sales Plans",["Company","Status","Target","Offer","Channel Plan"],
                      [(x["company_id"],x["status"],x["target_customer"],x["offer"],x["channel_plan"]) for x in CORE.db.rows("SELECT * FROM sales_plans ORDER BY updated_at DESC")]),
            "/lifecycle":("Lifecycle",["Company","State","Growth","Health","Next Action"],
                          [(x["company_id"],x["state"],x["growth_score"],x["health_score"],x["next_action"]) for x in CORE.db.rows("SELECT * FROM lifecycle ORDER BY growth_score DESC")]),
            "/reinvestment":("Reinvestment",["Company","Priority","Score","Recommendation","Status"],
                             [(x["company_id"],x["priority"],x["allocation_score"],x["recommendation"],x["status"]) for x in CORE.db.rows("SELECT * FROM reinvestment_recommendations ORDER BY priority DESC")]),
            "/activity":("Activity",["Time","Type","Source","Target"],
                         [(x["created_at"],x["event_type"],x["source"],x["target"]) for x in CORE.db.rows("SELECT * FROM events ORDER BY id DESC LIMIT 300")]),
        }
        if p in maps:
            t,h,r=maps[p]; return self.out(table(t,h,r))
        return self.out('{"error":"not_found"}',"application/json")

def loop():
    while True:
        time.sleep(60)
        try: CORE.cycle()
        except Exception as e: CORE.db.event("runtime.error","server",{"error":str(e)})

def main():
    CORE.migrate()
    threading.Thread(target=loop,daemon=True).start()
    print("CompanyOS V13 started: http://127.0.0.1:9000",flush=True)
    ThreadingHTTPServer(("127.0.0.1",9000),H).serve_forever()

if __name__=="__main__":
    main()
