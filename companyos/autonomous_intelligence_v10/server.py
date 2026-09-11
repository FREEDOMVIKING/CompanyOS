import json, threading, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from .core import AutonomousIntelligenceV10

CORE=AutonomousIntelligenceV10(Path.home()/"companyos")

def esc(s):
    s="" if s is None else str(s)
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def nav():
    return """<nav><a href="/">Overview</a><a href="/objectives">Objectives</a><a href="/companies">Companies</a>
<a href="/agents">Agents</a><a href="/decisions">Decisions</a><a href="/memory">Memory</a>
<a href="/opportunities">Opportunities</a><a href="/workforce">Workforce</a>
<a href="/improvements">Improvements</a><a href="/sandbox">Sandbox</a><a href="/plugins">Plugins</a>
<a href="/tasks">Tasks</a><a href="/activity">Activity</a></nav>"""

def page(title,body):
    return f"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="15"><title>{esc(title)}</title><style>
body{{font-family:system-ui;background:#07101f;color:#eef2ff;margin:0}}main{{max-width:1200px;margin:auto;padding:24px}}
nav{{display:flex;gap:10px;flex-wrap:wrap}}nav a{{color:#dbe8ff;text-decoration:none;background:#17233a;padding:10px 12px;border-radius:10px}}
.card{{background:#151d33;padding:20px;border-radius:18px;margin:16px 0}}.big{{font-size:42px;font-weight:800}}
table{{width:100%;border-collapse:collapse}}td,th{{padding:9px;border-bottom:1px solid #2a3550;text-align:left}}
</style></head><body><main>{nav()}<h1>{esc(title)}</h1>{body}</main></body></html>"""

def table(title,heads,rows):
    return page(title,'<div class="card"><table><tr>'+''.join(f'<th>{esc(h)}</th>' for h in heads)+'</tr>'+
                ''.join('<tr>'+''.join(f'<td>{esc(v)}</td>' for v in row)+'</tr>' for row in rows)+'</table></div>')

class H(BaseHTTPRequestHandler):
    def out(self,b,ctype="text/html; charset=utf-8"):
        if isinstance(b,str): b=b.encode()
        self.send_response(200); self.send_header("Content-Type",ctype); self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(b))); self.end_headers()
        try:self.wfile.write(b)
        except BrokenPipeError:pass

    def do_GET(self):
        p=urlparse(self.path).path
        if p=="/api/status": return self.out(json.dumps(CORE.status(),indent=2),"application/json")
        if p=="/api/cycle": return self.out(json.dumps(CORE.cycle(),indent=2),"application/json")
        if p=="/api/migrate": return self.out(json.dumps(CORE.migrate(),indent=2),"application/json")
        if p=="/":
            s=CORE.status()
            return self.out(page("CompanyOS Autonomous Intelligence V10",f"""
<div class="card"><div class="big">Autonomous Intelligence: ONLINE</div>
<p>Status: {esc(s['status'])}</p><p>Companies: {s['companies_total']}</p><p>Agents: {s['agents_total']}</p>
<p>Average company health: {s['average_company_health']}%</p><p>Top company: {esc(s['top_company'])}</p>
<p>Executive objectives: {s['executive_objectives_total']}</p><p>Executive memories: {s['executive_memories_total']}</p>
<p>Executive decisions: {s['executive_decisions_total']}</p><p>Opportunities: {s['opportunities_total']}</p>
<p>Workforce proposals: {s['workforce_proposals_total']}</p><p>Improvement proposals: {s['improvement_proposals_total']}</p>
<p>Sandbox validated: {s['sandbox_validated_total']}</p><p>Plugins: {s['plugins_total']}</p></div>
<div class="card"><h2>Runtime reliability</h2><p>Supervisor: supported</p><p>Watchdog restart: supported</p>
<p>Guaranteed survival if Android kills Termux: False</p></div>"""))
        maps={
            "/objectives":("Executive Objectives",["Days","Objective","Priority","Status"],
                [(x["horizon"],x["title"],x["priority"],x["status"]) for x in CORE.rows("SELECT * FROM objectives ORDER BY horizon")]),
            "/companies":("Companies",["Name","Status","Priority","Health"],
                [(x["name"],x["status"],x["priority"],x["health"]) for x in CORE.rows("SELECT * FROM companies ORDER BY priority DESC")]),
            "/agents":("Agents",["Name","Role","Company","Score"],
                [(x["name"],x["role"],x["company_id"],x["score"]) for x in CORE.rows("SELECT * FROM agents ORDER BY score DESC")]),
            "/decisions":("Decisions",["Subject","Decision","Confidence","Outcome"],
                [(x["subject"],x["decision"],x["confidence"],x["outcome_score"]) for x in CORE.rows("SELECT * FROM decisions ORDER BY updated_at DESC")]),
            "/memory":("Executive Memory V2",["Type","Subject","Company","Importance"],
                [(x["memory_type"],x["subject"],x["company_id"],x["importance"]) for x in CORE.rows("SELECT * FROM memories ORDER BY importance DESC")]),
            "/opportunities":("Opportunities",["Name","Category","Score","Status"],
                [(x["name"],x["category"],x["score"],x["status"]) for x in CORE.rows("SELECT * FROM opportunities ORDER BY score DESC")]),
            "/workforce":("Workforce",["Type","Agent","Company","Priority","Status"],
                [(x["proposal_type"],x["agent_id"],x["company_id"],x["priority"],x["status"]) for x in CORE.rows("SELECT * FROM workforce ORDER BY priority DESC")]),
            "/improvements":("Improvements",["Subject","Type","Priority","Risk","Status"],
                [(x["subject"],x["proposal_type"],x["priority"],x["risk"],x["status"]) for x in CORE.rows("SELECT * FROM improvements ORDER BY priority DESC")]),
            "/sandbox":("Sandbox",["Proposal","Status","Score"],
                [(x["proposal_id"],x["status"],x["score"]) for x in CORE.rows("SELECT * FROM sandbox ORDER BY updated_at DESC")]),
            "/plugins":("Plugins",["Name","Status","Capabilities"],
                [(x["name"],x["status"],x["capabilities"]) for x in CORE.rows("SELECT * FROM plugins ORDER BY name")]),
            "/tasks":("Tasks",["Task","Company","Status","Priority"],
                [(x["title"],x["company_id"],x["status"],x["priority"]) for x in CORE.rows("SELECT * FROM tasks ORDER BY updated_at DESC LIMIT 500")]),
            "/activity":("Activity",["Time","Type","Source","Target"],
                [(x["created_at"],x["event_type"],x["source"],x["target"]) for x in CORE.rows("SELECT * FROM events ORDER BY id DESC LIMIT 500")]),
        }
        if p in maps:
            title,heads,rows=maps[p]
            return self.out(table(title,heads,rows))
        return self.out('{"error":"not_found"}',"application/json")

def loop():
    while True:
        time.sleep(30)
        try: CORE.cycle()
        except Exception as e: CORE.event("runtime.error","server",{"error":str(e)})

def main():
    CORE.cycle()
    threading.Thread(target=loop,daemon=True).start()
    print("CompanyOS Autonomous Intelligence V10 started: http://127.0.0.1:9000",flush=True)
    ThreadingHTTPServer(("127.0.0.1",9000),H).serve_forever()

if __name__=="__main__":
    main()
