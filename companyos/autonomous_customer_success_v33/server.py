
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from .engine import CustomerSuccessV33

HOST,PORT="127.0.0.1",8795
E=CustomerSuccessV33(Path.home()/"companyos")

def html():
    s=E.run_cycle()
    return f'''<!doctype html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{{font-family:system-ui;background:#08101f;color:#eef2ff;margin:0}}
main{{max-width:1000px;margin:auto;padding:30px 20px}}
.card{{background:#151d33;padding:24px;border-radius:18px;margin-bottom:18px}}
.big{{font-size:36px;font-weight:800}}
</style></head><body><main>
<h1>CompanyOS Autonomous Customer Success & Support</h1>
<section class="card">
<p>Status: {s["status"]}</p>
<p class="big">Customers: {s["customers_total"]}</p>
<p>Orders: {s["orders_total"]}</p>
<p>Paid orders: {s["paid_orders"]}</p>
<p>Open tickets: {s["tickets_open"]}</p>
<p>Knowledge articles: {s["knowledge_articles"]}</p>
<p>Follow-ups queued: {s["followups_queued"]}</p>
<p>Refunds pending review: {s["refunds_pending_review"]}</p>
<p>Automatic external messages: {s["automatic_external_messages_enabled"]}</p>
<p>Automatic refunds: {s["automatic_refunds_enabled"]}</p>
</section></main></body></html>'''

class H(BaseHTTPRequestHandler):
    def j(self,obj,code=200):
        b=json.dumps(obj,indent=2).encode()
        self.send_response(code); self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        p=urlparse(self.path).path
        if p=="/api/status": return self.j(E.run_cycle())
        if p in ("/","/index.html"):
            b=html().encode()
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b); return
        self.j({"error":"not_found"},404)

def main():
    E.run_cycle()
    print("CompanyOS Autonomous Customer Success & Support V33 started: http://127.0.0.1:8795",flush=True)
    ThreadingHTTPServer((HOST,PORT),H).serve_forever()

if __name__=="__main__": main()
