import json,threading,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,parse_qs
from .core import ExternalIntegrationExecutionV15
CORE=ExternalIntegrationExecutionV15(Path.home()/'companyos')
def esc(s): return str(s if s is not None else '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
def page(t,b): return f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{{font-family:system-ui;background:#07101f;color:#eef2ff;padding:24px}}a{{color:#cfe0ff}}nav{{display:flex;gap:12px;flex-wrap:wrap}}.card{{background:#151d33;padding:20px;border-radius:18px;margin-top:18px}}table{{width:100%}}td,th{{padding:8px;text-align:left}}</style></head><body><nav><a href="/">Overview</a><a href="/connectors">Connectors</a><a href="/actions">Actions</a><a href="/receipts">Receipts</a><a href="/audit">Audit</a></nav><h1>{esc(t)}</h1>{b}</body></html>'
def table(t,h,r): return page(t,'<div class="card"><table><tr>'+''.join(f'<th>{esc(x)}</th>' for x in h)+'</tr>'+''.join('<tr>'+''.join(f'<td>{esc(v)}</td>' for v in row)+'</tr>' for row in r)+'</table></div>')
class H(BaseHTTPRequestHandler):
 def out(self,b,ctype='text/html; charset=utf-8'):
  if isinstance(b,str): b=b.encode('utf-8')
  self.send_response(200); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
 def do_GET(self):
  p=urlparse(self.path); path=p.path
  if path=='/api/status': return self.out(json.dumps(CORE.status(),indent=2),'application/json')
  if path=='/api/cycle': return self.out(json.dumps(CORE.cycle(),indent=2),'application/json')
  if path=='/api/approve': return self.out(json.dumps(CORE.approve((parse_qs(p.query).get('action_id') or [''])[0]),indent=2),'application/json')
  if path=='/':
   s=CORE.status(); return self.out(page('CompanyOS External Integration & Execution V15',f'<div class="card"><h2>Integration & Execution: ONLINE</h2><p>Company builds: {s["company_builds_total"]}</p><p>Connectors configured: {s["connectors_configured"]}/{s["connectors_total"]}</p><p>Healthy connectors: {s["connectors_healthy"]}</p><p>Actions awaiting review: {s["actions_review_required"]}</p><p>Actions executed: {s["actions_executed"]}</p><p>Receipts: {s["execution_receipts_total"]}</p></div>'))
  if path=='/connectors': return self.out(table('Connectors',['Name','Category','Mode','Status'],[(x['name'],x['category'],x['mode'],x['status']) for x in CORE.rows('SELECT * FROM connectors ORDER BY name')]))
  if path=='/actions': return self.out(table('Actions',['ID','Company','Action','Risk','Connector','Status'],[(x['action_id'],x['company_id'],x['action_type'],x['risk_level'],x['connector_name'],x['status']) for x in CORE.rows('SELECT * FROM action_queue')]))
  if path=='/receipts': return self.out(table('Receipts',['Time','Company','Connector','Status','Ref'],[(x['created_at'],x['company_id'],x['connector_name'],x['status'],x['external_ref']) for x in CORE.rows('SELECT * FROM receipts ORDER BY created_at DESC')]))
  if path=='/audit': return self.out(table('Audit',['Time','Company','Event','Actor','Decision'],[(x['created_at'],x['company_id'],x['event_type'],x['actor'],x['decision']) for x in CORE.rows('SELECT * FROM audit ORDER BY id DESC')]))
  return self.out('{"error":"not_found"}','application/json')
def loop():
 while True:
  time.sleep(60)
  try: CORE.cycle()
  except Exception: pass
def main():
 CORE.migrate(); CORE.sync_connectors(); threading.Thread(target=loop,daemon=True).start(); print('CompanyOS V15 started: http://127.0.0.1:9000',flush=True); ThreadingHTTPServer(('127.0.0.1',9000),H).serve_forever()
if __name__=='__main__': main()
