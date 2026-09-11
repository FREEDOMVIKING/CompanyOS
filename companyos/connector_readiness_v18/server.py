import json, threading, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from .core import ConnectorReadinessV18

CORE=ConnectorReadinessV18(Path.home()/"companyos")
def e(s):return str("" if s is None else s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
def page(title,body):
    nav='<nav><a href="/">Overview</a><a href="/connectors">Connectors</a><a href="/actions">Action Readiness</a><a href="/audit">Audit</a></nav>'
    return f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{{font-family:system-ui;background:#07101f;color:#eef2ff;margin:0}}main{{max-width:1200px;margin:auto;padding:24px}}nav{{display:flex;gap:10px;flex-wrap:wrap}}nav a{{color:#dbe8ff;text-decoration:none;background:#17233a;padding:10px 12px;border-radius:10px}}.card{{background:#151d33;padding:20px;border-radius:18px;margin:16px 0}}table{{width:100%;border-collapse:collapse}}td,th{{padding:9px;border-bottom:1px solid #2a3550;text-align:left}}</style></head><body><main>{nav}<h1>{e(title)}</h1>{body}</main></body></html>'
def table(title,heads,rows):
    return page(title,'<div class="card"><table><tr>'+''.join(f'<th>{e(h)}</th>' for h in heads)+'</tr>'+''.join('<tr>'+''.join(f'<td>{e(v)}</td>' for v in r)+'</tr>' for r in rows)+'</table></div>')

class H(BaseHTTPRequestHandler):
    def out(self,b,ctype="text/html; charset=utf-8"):
        if isinstance(b,str):b=b.encode()
        self.send_response(200);self.send_header("Content-Type",ctype);self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def do_GET(self):
        p=self.path.split("?")[0]
        if p=="/api/status":return self.out(json.dumps(CORE.status(),indent=2),"application/json")
        if p=="/api/cycle":return self.out(json.dumps(CORE.cycle(),indent=2),"application/json")
        if p=="/":
            s=CORE.status()
            return self.out(page("CompanyOS Connector Configuration & Credential Readiness V18",
                f'<div class="card"><h2>Connector Readiness: ONLINE</h2><p>Actions: {s["actions_total"]}</p><p>Connectors: {s["connectors_total"]}</p><p>Enabled: {s["connectors_enabled"]}</p><p>Credentials ready: {s["credentials_ready"]}</p><p>Healthy: {s["connectors_healthy"]}</p><p>Configured, untested: {s["connectors_configured_untested"]}</p><p>Eligible non-financial actions: {s["actions_eligible_for_nonfinancial_execution"]}</p><p>Financial automation: {s["financial_automation"]}</p></div>'))
        if p=="/connectors":
            return self.out(table("Connectors",["Name","Provider","Enabled","Status","Credentials","Health","Missing env","Error"],[(x["name"],x["provider"],x["enabled"],x["status"],x["credential_state"],x["health_state"],x["missing_env"],x["last_error"]) for x in CORE._rows("select * from connectors order by name")]))
        if p=="/actions":
            return self.out(table("Action Readiness",["Action ID","Type","Status","Connector","Credentials","Eligible","Blocker"],[(x["action_id"],x["action_type"],x["action_status"],x["connector_status"],x["credential_state"],x["eligible"],x["blocker"]) for x in CORE._rows("select * from action_readiness order by action_type,action_id")]))
        if p=="/audit":
            return self.out(table("Audit",["Time","Event","Payload"],[(x["created_at"],x["event_type"],x["payload_json"]) for x in CORE._rows("select * from audit order by id desc limit 200")]))
        return self.out('{"error":"not_found"}',"application/json")

def loop():
    while True:
        time.sleep(60)
        try:CORE.cycle()
        except Exception:pass
def main():
    CORE.cycle();threading.Thread(target=loop,daemon=True).start()
    print("CompanyOS V18 started: http://127.0.0.1:9000",flush=True)
    ThreadingHTTPServer(("127.0.0.1",9000),H).serve_forever()
if __name__=="__main__":main()
