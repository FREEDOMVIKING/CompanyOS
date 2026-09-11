import json, threading, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse
from .core import OpportunityIntelligenceV11

CORE=OpportunityIntelligenceV11(Path.home()/"companyos")

def e(s):
    s="" if s is None else str(s)
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def nav():
    return """<nav><a href="/">Overview</a><a href="/sources">Sources</a><a href="/research">Research</a>
<a href="/opportunities">Opportunities</a><a href="/validation">Validation</a>
<a href="/proposals">Venture Proposals</a><a href="/activity">Activity</a></nav>"""

def page(title,body):
    return f"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="20"><title>{e(title)}</title><style>
body{{font-family:system-ui;background:#07101f;color:#eef2ff;margin:0}}main{{max-width:1200px;margin:auto;padding:24px}}
nav{{display:flex;gap:10px;flex-wrap:wrap}}nav a{{color:#dbe8ff;text-decoration:none;background:#17233a;padding:10px 12px;border-radius:10px}}
.card{{background:#151d33;padding:20px;border-radius:18px;margin:16px 0}}.big{{font-size:42px;font-weight:800}}
table{{width:100%;border-collapse:collapse}}td,th{{padding:9px;border-bottom:1px solid #2a3550;text-align:left}}
</style></head><body><main>{nav()}<h1>{e(title)}</h1>{body}</main></body></html>"""

def table(title,heads,rows):
    return page(title,'<div class="card"><table><tr>'+''.join(f'<th>{e(h)}</th>' for h in heads)+'</tr>'+
                ''.join('<tr>'+''.join(f'<td>{e(v)}</td>' for v in r)+'</tr>' for r in rows)+'</table></div>')

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
            return self.out(page("CompanyOS Autonomous Opportunity Intelligence V11",f"""
<div class="card"><div class="big">Opportunity Intelligence: ONLINE</div>
<p>Status: {e(s['status'])}</p><p>Companies: {s['companies_total']}</p><p>Agents: {s['agents_total']}</p>
<p>Research sources: {s['research_sources_total']} ({s['research_sources_enabled']} enabled)</p>
<p>Healthy sources: {s['research_sources_healthy']}</p><p>Research items: {s['research_items_total']}</p>
<p>Opportunities: {s['opportunities_total']}</p><p>Executive review: {s['executive_review_opportunities']}</p>
<p>Validation queue: {s['validation_queue_total']}</p><p>Venture proposals: {s['venture_proposals_total']}</p>
<p>Top opportunity: {e(s['top_opportunity'])} ({s['top_opportunity_score']})</p></div>
<div class="card"><h2>Research runtime</h2><p>Continuous research: True</p>
<p>Automatic external launch: False</p></div>"""))
        if p=="/sources":
            rows=[(x["name"],x["source_type"],x["enabled"],x["status"],x["last_http_status"],x["last_error"])
                  for x in CORE.db.rows("SELECT * FROM research_sources ORDER BY name")]
            return self.out(table("Research Sources",["Name","Type","Enabled","Status","HTTP","Error"],rows))
        if p=="/research":
            rows=[(x["title"],x["category"],x["published_at"],x["url"]) for x in CORE.db.rows("SELECT * FROM research_items ORDER BY created_at DESC LIMIT 300")]
            return self.out(table("Research Items",["Title","Category","Published","URL"],rows))
        if p=="/opportunities":
            rows=[(x["name"],x["category"],x["total_score"],x["evidence_count"],x["status"])
                  for x in CORE.db.rows("SELECT * FROM opportunity_candidates ORDER BY total_score DESC")]
            return self.out(table("Opportunities",["Name","Category","Score","Evidence","Status"],rows))
        if p=="/validation":
            rows=[(x["opportunity_id"],x["priority"],x["status"],x["hypothesis"])
                  for x in CORE.db.rows("SELECT * FROM validation_queue ORDER BY priority DESC")]
            return self.out(table("Validation Queue",["Opportunity","Priority","Status","Hypothesis"],rows))
        if p=="/proposals":
            rows=[(x["name"],x["score"],x["status"],x["rationale"])
                  for x in CORE.db.rows("SELECT * FROM venture_proposals ORDER BY score DESC")]
            return self.out(table("Venture Proposals",["Name","Score","Status","Rationale"],rows))
        if p=="/activity":
            rows=[(x["created_at"],x["event_type"],x["source"],x["target"])
                  for x in CORE.db.rows("SELECT * FROM events ORDER BY id DESC LIMIT 300")]
            return self.out(table("Activity",["Time","Type","Source","Target"],rows))
        return self.out('{"error":"not_found"}',"application/json")

def loop():
    while True:
        time.sleep(60)
        try: CORE.cycle()
        except Exception as ex: CORE.db.event("runtime.error","server",{"error":str(ex)})

def main():
    CORE.migrate()
    CORE.sources.sync()
    threading.Thread(target=loop,daemon=True).start()
    print("CompanyOS V11 started: http://127.0.0.1:9000",flush=True)
    ThreadingHTTPServer(("127.0.0.1",9000),H).serve_forever()

if __name__=="__main__":
    main()
