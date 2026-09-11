import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .engine import CRM
E=CRM(Path.home()/'companyos')
def page():
 s=E.cycle();cards=''.join(f"<article><h2>{c.get('email')}</h2><p>Segment: {c.get('segment')}</p><p>Paid orders: {c.get('paid_orders')}</p><p>Lifetime value: ${c.get('lifetime_value_usd')}</p><p>Referral: {c.get('referral_code')}</p></article>" for c in E.index().get('customers',{}).values()) or '<article><h2>No customers yet</h2><p>Profiles appear after checkout activity.</p></article>'
 return f"<!doctype html><meta name=viewport content='width=device-width,initial-scale=1'><style>body{{font-family:system-ui;background:#0b1020;color:#eef2ff;margin:0}}main{{max-width:900px;margin:auto;padding:30px 20px}}.s,article{{background:#151d33;padding:20px;border-radius:18px;margin:18px 0}}</style><main><h1>CompanyOS Customer Growth & CRM</h1><div class=s><p>Status: {s['status']}</p><p>Customers: {s['customers_total']}</p><p>Leads: {s['leads']}</p><p>Paying customers: {s['paying_customers']}</p><p>Open tickets: {s['open_support_tickets']}</p></div>{cards}</main>"
class H(BaseHTTPRequestHandler):
 def j(self,x,c=200):
  b=json.dumps(x,indent=2,default=str).encode();self.send_response(c);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
 def do_GET(self):
  p=urlparse(self.path).path
  if p=='/api/status':self.j(E.cycle())
  elif p=='/api/customers':self.j(E.index())
  elif p=='/api/tickets':self.j(E.tickets())
  elif p in ('/','/index.html'):
   b=page().encode();self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
  else:self.j({'error':'not_found'},404)
 def do_POST(self):
  if urlparse(self.path).path!='/api/tickets':self.j({'error':'not_found'},404);return
  n=int(self.headers.get('Content-Length','0'));p=json.loads(self.rfile.read(n) or b'{}');self.j({'ok':True,'ticket':E.create_ticket(str(p.get('email','')),str(p.get('subject','')),str(p.get('message','')))},201)
def main():E.cycle();print('CompanyOS CRM V13 started: http://127.0.0.1:8775',flush=True);ThreadingHTTPServer(('127.0.0.1',8775),H).serve_forever()
if __name__=='__main__':main()
