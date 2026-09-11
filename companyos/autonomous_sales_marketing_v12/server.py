import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .engine import Engine
E=Engine(Path.home()/'companyos')
def html():
    s=E.run(); q=E.queue(); cards=''.join(f"<article><h2>{c.get('name')}</h2><p>Priority: {c.get('priority_score')}</p><p>Current ${c.get('pricing',{}).get('current')} → Recommended ${c.get('pricing',{}).get('recommended')}</p><p>{c.get('pricing',{}).get('reason')}</p><code>{c.get('asset_folder')}</code></article>" for c in q.get('campaigns',[]))
    return f'<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{{font-family:system-ui;background:#0b1020;color:#eef2ff;margin:0}}main{{max-width:1000px;margin:auto;padding:30px 20px}}article,.box{{background:#151d33;padding:20px;border-radius:18px;margin-bottom:18px}}code{{word-break:break-word;color:#a9c4ff}}</style><main><h1>CompanyOS Sales & Marketing Engine</h1><div class="box"><p>Status: {s.get("status")}</p><p>Products: {s.get("products_analyzed")}</p><p>Campaigns: {s.get("campaigns_ready")}</p><p>External publishing: review required</p></div>{cards}</main>'
class H(BaseHTTPRequestHandler):
    def sendj(self,obj,code=200):
        b=json.dumps(obj,indent=2,default=str).encode(); self.send_response(code); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        p=urlparse(self.path).path
        if p=='/api/status': self.sendj(E.run())
        elif p=='/api/campaigns': self.sendj(E.queue())
        elif p in ('/','/index.html'):
            b=html().encode(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
        else: self.sendj({'error':'not_found'},404)
def main():
    E.run(); print('CompanyOS Autonomous Sales & Marketing V12 started: http://127.0.0.1:8774',flush=True); ThreadingHTTPServer(('127.0.0.1',8774),H).serve_forever()
if __name__=='__main__': main()
