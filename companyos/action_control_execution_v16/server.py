import json, threading, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from .core import ActionControlExecutionV16
CORE=ActionControlExecutionV16(Path.home()/"companyos")

def e(s): return str("" if s is None else s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
def page(title,body):
    nav='<nav><a href="/">Overview</a><a href="/connectors">Connectors</a><a href="/actions">Actions</a><a href="/receipts">Receipts</a><a href="/scores">Scores</a><a href="/audit">Audit</a></nav>'
    return f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{{font-family:system-ui;background:#07101f;color:#eef2ff;margin:0}}main{{max-width:1200px;margin:auto;padding:24px}}nav{{display:flex;gap:10px;flex-wrap:wrap}}nav a,a.button{{color:#dbe8ff;text-decoration:none;background:#17233a;padding:10px 12px;border-radius:10px}}.card{{background:#151d33;padding:20px;border-radius:18px;margin:16px 0}}table{{width:100%;border-collapse:collapse}}td,th{{padding:9px;border-bottom:1px solid #2a3550;text-align:left}}</style></head><body><main>{nav}<h1>{e(title)}</h1>{body}</main></body></html>'
def table(title,heads,rows):
    h='<tr>'+''.join(f'<th>{e(x)}</th>' for x in heads)+'</tr>'
    b=''.join('<tr>'+''.join(f'<td>{v if isinstance(v,str) and v.startswith("<a ") else e(v)}</td>' for v in r)+'</tr>' for r in rows)
    return page(title,f'<div class="card"><table>{h}{b}</table></div>')

class H(BaseHTTPRequestHandler):
    def out(self,b,ctype="text/html; charset=utf-8"):
        if isinstance(b,str): b=b.encode()
        self.send_response(200); self.send_header("Content-Type",ctype); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        q=urlparse(self.path); p=q.path; a=parse_qs(q.query)
        if p=="/api/status": return self.out(json.dumps(CORE.status(),indent=2),"application/json")
        if p=="/api/cycle": return self.out(json.dumps(CORE.cycle(),indent=2),"application/json")
        if p=="/api/approve": return self.out(json.dumps(CORE.executor.approve((a.get("action_id") or [""])[0]),indent=2),"application/json")
        if p=="/api/approve-safe-batch": return self.out(json.dumps(CORE.executor.approve_safe_batch(),indent=2),"application/json")
        if p=="/api/retry": return self.out(json.dumps(CORE.executor.retry((a.get("action_id") or [""])[0]),indent=2),"application/json")
        if p=="/":
            s=CORE.status()
            return self.out(page("CompanyOS Action Control & Execution V16",f'<div class="card"><h2>Action Control & Execution: ONLINE</h2><p>Company builds: {s["company_builds_total"]}</p><p>Connectors configured: {s["connectors_configured"]}/{s["connectors_total"]}</p><p>Healthy connectors: {s["connectors_healthy"]}</p><p>Actions awaiting review: {s["actions_review_required"]}</p><p>Approved: {s["actions_approved"]}</p><p>Executed: {s["actions_executed"]}</p><p>Failed: {s["actions_failed"]}</p><p>Policy blocked: {s["actions_policy_blocked"]}</p><p>Receipts: {s["receipts_total"]}</p><p><a class="button" href="/api/approve-safe-batch">Approve safe non-financial batch</a></p></div>'))
        if p=="/connectors":
            return self.out(table("Connectors",["Name","Category","Mode","Status","Error"],[(x["name"],x["category"],x["mode"],x["status"],x["last_error"]) for x in CORE.db.rows("SELECT * FROM connectors ORDER BY name")]))
        if p=="/actions":
            rows=[]
            for x in CORE.db.rows("SELECT * FROM actions ORDER BY company_id,action_type"):
                ctl=""
                if x["status"]=="REVIEW_REQUIRED": ctl=f'<a class="button" href="/api/approve?action_id={x["action_id"]}">Approve</a>'
                elif x["status"] in ("FAILED","HTTP_ERROR","CONNECTOR_ERROR","CONNECTOR_NOT_LIVE","CONNECTOR_DISABLED","NO_BUILD","MISSING_SITE"): ctl=f'<a class="button" href="/api/retry?action_id={x["action_id"]}">Retry</a>'
                rows.append((x["action_id"],x["company_id"],x["action_type"],x["risk_level"],x["connector_name"],x["status"],x["policy_decision"],x["attempts"],ctl))
            return self.out(table("Actions",["Action ID","Company","Action","Risk","Connector","Status","Policy","Attempts","Control"],rows))
        if p=="/receipts":
            return self.out(table("Receipts",["Time","Company","Connector","Status","External Ref"],[(x["created_at"],x["company_id"],x["connector_name"],x["status"],x["external_ref"]) for x in CORE.db.rows("SELECT * FROM receipts ORDER BY created_at DESC")]))
        if p=="/scores":
            return self.out(table("Execution Scores",["Company","Success","Failure","Blocked","Score","Last"],[(x["company_id"],x["successes"],x["failures"],x["blocked"],x["execution_score"],x["last_result"]) for x in CORE.db.rows("SELECT * FROM execution_scores ORDER BY execution_score DESC")]))
        if p=="/audit":
            return self.out(table("Audit",["Time","Company","Event","Actor","Decision"],[(x["created_at"],x["company_id"],x["event_type"],x["actor"],x["decision"]) for x in CORE.db.rows("SELECT * FROM audit_log ORDER BY id DESC LIMIT 400")]))
        return self.out('{"error":"not_found"}',"application/json")

def loop():
    while True:
        time.sleep(60)
        try: CORE.cycle()
        except Exception: pass
def main():
    CORE.migrate(); CORE.connectors.sync()
    threading.Thread(target=loop,daemon=True).start()
    print("CompanyOS V16 started: http://127.0.0.1:9000",flush=True)
    ThreadingHTTPServer(("127.0.0.1",9000),H).serve_forever()
if __name__=="__main__": main()
