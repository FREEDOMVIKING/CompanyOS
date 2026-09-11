
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .engine import FinanceV30
HOST,PORT="127.0.0.1",8792
E=FinanceV30(Path.home()/"companyos")

def html():
    s=E.run_cycle(); p=s["pnl"]
    budgets="".join(f"<article><h2>{b.get('name')}</h2><p>Score: {b.get('portfolio_score')}</p><p>Suggested test budget: ${b.get('suggested_test_budget_usd')}</p><p>Approval required: {b.get('requires_approval')}</p></article>" for b in s["venture_budgets"])
    return f"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>
body{{font-family:system-ui;background:#08101f;color:#eef2ff;margin:0}}main{{max-width:1000px;margin:auto;padding:30px 20px}}
section,article{{background:#151d33;padding:22px;border-radius:18px;margin-bottom:18px}}.big{{font-size:34px;font-weight:800}}
</style></head><body><main><h1>CompanyOS Autonomous Finance & Treasury</h1><section>
<p>Status: {s['status']}</p><p class="big">Net Profit: ${p['net_profit_usd']}</p>
<p>Revenue: ${p['revenue_usd']}</p><p>Expenses: ${p['expenses_usd']}</p>
<p>Ledger entries: {s['ledger_entries']}</p><p>Treasury wallet detected: {s['treasury_wallet_detected']}</p>
<p>Automatic transfers: {s['automatic_transfers_enabled']}</p><p>Automatic spending: {s['automatic_spending_enabled']}</p>
</section><h2>Venture Budgets</h2>{budgets or '<article>No venture budgets yet.</article>'}</main></body></html>"""

class H(BaseHTTPRequestHandler):
    def sj(self,obj,c=200):
        b=json.dumps(obj,indent=2).encode(); self.send_response(c); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        p=urlparse(self.path).path
        if p=="/api/status": return self.sj(E.run_cycle())
        if p=="/api/ledger": return self.sj({"entries":E.ledger()})
        if p in ("/","/index.html"):
            b=html().encode(); self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b); return
        self.sj({"error":"not_found"},404)
def main():
    E.run_cycle(); print("CompanyOS Autonomous Finance & Treasury V30 started: http://127.0.0.1:8792",flush=True); ThreadingHTTPServer((HOST,PORT),H).serve_forever()
if __name__=="__main__": main()
