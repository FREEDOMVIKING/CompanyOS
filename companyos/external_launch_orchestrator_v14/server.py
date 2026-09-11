import json, threading, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .core import ExternalLaunchOrchestratorV14
CORE=ExternalLaunchOrchestratorV14(Path.home()/"companyos")

def esc(s): return str(s if s is not None else "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
def table(title,heads,rows):
    nav='<p><a href="/">Overview</a> · <a href="/readiness">Readiness</a> · <a href="/domains">Domains</a> · <a href="/connectors">Connectors</a> · <a href="/actions">Actions</a></p>'
    body='<table><tr>'+''.join(f'<th>{esc(h)}</th>' for h in heads)+'</tr>'+''.join('<tr>'+''.join(f'<td>{esc(v)}</td>' for v in r)+'</tr>' for r in rows)+'</table>'
    return f'<!doctype html><meta name="viewport" content="width=device-width"><style>body{{font-family:system-ui;background:#07101f;color:#eef2ff;padding:24px}}a{{color:#bcd6ff}}.card{{background:#151d33;padding:20px;border-radius:18px}}table{{width:100%}}td,th{{padding:8px;text-align:left}}</style>{nav}<h1>{esc(title)}</h1><div class="card">{body}</div>'

class H(BaseHTTPRequestHandler):
    def send(self,b,ctype="text/html"):
        if isinstance(b,str): b=b.encode()
        self.send_response(200); self.send_header("Content-Type",ctype); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        p=self.path.split("?")[0]
        if p=="/api/status": return self.send(json.dumps(CORE.status(),indent=2),"application/json")
        if p=="/api/cycle": return self.send(json.dumps(CORE.cycle(),indent=2),"application/json")
        if p=="/":
            s=CORE.status()
            return self.send(table("CompanyOS External Launch Orchestrator V14",["Metric","Value"],[
              ("Status",s["external_launch_orchestrator"]),("Company builds",s["company_builds_total"]),
              ("Launch ready",s["launch_ready_total"]),("Deployment manifests",s["deployment_manifests_total"]),
              ("Domain suggestions",s["domain_suggestions_total"]),("DNS plans",s["dns_plans_total"]),
              ("Storefront plans",s["storefront_plans_total"]),("Acquisition plans",s["acquisition_plans_total"]),
              ("Actions awaiting review",s["external_actions_review_required"]),("Connectors configured",f'{s["connectors_configured"]}/{s["connectors_total"]}')
            ]))
        if p=="/readiness": return self.send(table("Launch Readiness",["Company","Score","Status","Blockers"],[(x["company_name"],x["score"],x["status"],x["blockers_json"]) for x in CORE.rows("SELECT * FROM readiness ORDER BY score DESC")]))
        if p=="/domains": return self.send(table("Domain Suggestions",["Company","Candidate","Status"],[(x["company_id"],x["candidate"],x["status"]) for x in CORE.rows("SELECT * FROM domains")]))
        if p=="/connectors": return self.send(table("Connectors",["Name","Category","Status","Required"],[(x["name"],x["category"],x["status"],x["required"]) for x in CORE.rows("SELECT * FROM connectors")]))
        if p=="/actions": return self.send(table("External Action Queue",["Company","Action","Risk","Connector","Status"],[(x["company_id"],x["action_type"],x["risk"],x["connector"],x["status"]) for x in CORE.rows("SELECT * FROM action_queue")]))
        self.send('{"error":"not_found"}',"application/json")

def loop():
    while True:
        time.sleep(60)
        try: CORE.cycle()
        except Exception: pass

def main():
    CORE.migrate(); threading.Thread(target=loop,daemon=True).start()
    print("CompanyOS V14 started: http://127.0.0.1:9000",flush=True)
    ThreadingHTTPServer(("127.0.0.1",9000),H).serve_forever()
if __name__=="__main__": main()
