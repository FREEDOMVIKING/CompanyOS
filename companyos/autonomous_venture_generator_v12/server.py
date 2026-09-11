import json, threading, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse
from .core import AutonomousVentureGeneratorV12

CORE=AutonomousVentureGeneratorV12(Path.home()/"companyos")

def esc(s):
    s="" if s is None else str(s)
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def nav():
    return """<nav><a href="/">Overview</a><a href="/proposals">Venture Proposals</a>
<a href="/plans">Business Plans</a><a href="/milestones">Milestones</a>
<a href="/launch">Launch Packages</a><a href="/reviews">Executive Review</a>
<a href="/handoffs">Company Handoffs</a><a href="/activity">Activity</a></nav>"""

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
            return self.out(page("CompanyOS Autonomous Venture Generator V12",f"""
<div class="card"><div class="big">Venture Generator: ONLINE</div>
<p>Status: {esc(s['status'])}</p><p>Companies: {s['companies_total']}</p><p>Agents: {s['agents_total']}</p>
<p>Opportunities: {s['opportunities_total']}</p><p>Venture proposals: {s['venture_proposals_total']}</p>
<p>Business plans: {s['business_plans_total']}</p><p>Milestones: {s['milestones_total']}</p>
<p>Launch packages: {s['launch_packages_total']}</p><p>Executive reviews: {s['executive_reviews_total']}</p>
<p>Company handoffs: {s['company_handoffs_total']}</p>
<p>Top venture: {esc(s['top_venture'])} ({s['top_venture_score']})</p></div>
<div class="card"><h2>Execution gates</h2>
<p>Automatic external launch: False</p><p>Automatic company creation: False</p></div>"""))
        if p=="/proposals":
            rows=[(x["name"],x["venture_score"],x["business_model"],x["revenue_model"],x["risk_level"],x["status"])
                  for x in CORE.db.rows("SELECT * FROM venture_proposals ORDER BY venture_score DESC")]
            return self.out(table("Venture Proposals",["Name","Score","Business Model","Revenue","Risk","Status"],rows))
        if p=="/plans":
            rows=[(x["proposal_id"],x["customer"],x["offer"],x["go_to_market"])
                  for x in CORE.db.rows("SELECT * FROM business_plans ORDER BY updated_at DESC")]
            return self.out(table("Business Plans",["Proposal","Customer","Offer","Go-to-market"],rows))
        if p=="/milestones":
            rows=[(x["proposal_id"],x["sequence_no"],x["title"],x["success_criteria"],x["status"])
                  for x in CORE.db.rows("SELECT * FROM milestones ORDER BY proposal_id,sequence_no")]
            return self.out(table("Milestones",["Proposal","Seq","Milestone","Success Criteria","Status"],rows))
        if p=="/launch":
            rows=[(x["proposal_id"],x["launch_score"],x["status"])
                  for x in CORE.db.rows("SELECT * FROM launch_packages ORDER BY launch_score DESC")]
            return self.out(table("Launch Packages",["Proposal","Score","Status"],rows))
        if p=="/reviews":
            rows=[(x["proposal_id"],x["priority"],x["recommendation"],x["status"])
                  for x in CORE.db.rows("SELECT * FROM executive_review ORDER BY priority DESC")]
            return self.out(table("Executive Review",["Proposal","Priority","Recommendation","Status"],rows))
        if p=="/handoffs":
            rows=[(x["company_name"],x["proposal_id"],x["status"])
                  for x in CORE.db.rows("SELECT * FROM company_handoffs ORDER BY updated_at DESC")]
            return self.out(table("Company Handoffs",["Company","Proposal","Status"],rows))
        if p=="/activity":
            rows=[(x["created_at"],x["event_type"],x["source"],x["target"])
                  for x in CORE.db.rows("SELECT * FROM events ORDER BY id DESC LIMIT 300")]
            return self.out(table("Activity",["Time","Type","Source","Target"],rows))
        return self.out('{"error":"not_found"}',"application/json")

def loop():
    while True:
        time.sleep(60)
        try: CORE.cycle()
        except Exception as e: CORE.db.event("runtime.error","server",{"error":str(e)})

def main():
    CORE.migrate()
    threading.Thread(target=loop,daemon=True).start()
    print("CompanyOS V12 started: http://127.0.0.1:9000",flush=True)
    ThreadingHTTPServer(("127.0.0.1",9000),H).serve_forever()

if __name__=="__main__":
    main()
