
import json, os, tempfile
from pathlib import Path
from datetime import datetime, timezone

def now(): return datetime.now(timezone.utc).isoformat()

def rj(p,d=None):
    if d is None: d={}
    try: return json.loads(Path(p).read_text())
    except Exception: return d

def wj(p,d):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=str(p.parent),prefix=p.name+".")
    with os.fdopen(fd,"w") as f: json.dump(d,f,indent=2,sort_keys=True)
    os.replace(tmp,p)

class FinanceV30:
    def __init__(self,home):
        self.home=Path(home); self.live=self.home/".companyos_runtime"
        self.rec=self.home/"finance_treasury_records_v30"
        self.run=self.home/"companyos_runtime/autonomous_finance_treasury_v30_1200001_1250000"
        for p in (self.live,self.rec,self.run): p.mkdir(parents=True,exist_ok=True)

    def orders(self):
        return rj(self.home/"storefront_sales_records_v29/orders.json",{"orders":[]}).get("orders",[])

    def expenses(self):
        return rj(self.live/"finance_expenses_v30.json",{"expenses":[]}).get("expenses",[])

    def ledger(self):
        out=[]
        for o in self.orders():
            if o.get("payment_status")=="PAID_VERIFIED":
                out.append({"type":"REVENUE","ref":o.get("order_id"),"unit":o.get("product_id"),
                            "amount_usd":float(o.get("amount_usd",0) or 0),"verified":True})
        for e in self.expenses():
            out.append({"type":"EXPENSE","ref":e.get("reference"),"unit":e.get("venture_id") or e.get("product_id"),
                        "amount_usd":float(e.get("amount_usd",0) or 0),"verified":bool(e.get("verified",False)),
                        "category":e.get("category")})
        return out

    def budgets(self):
        portfolio=rj(self.live/"autonomous_revenue_expansion_v26_live.json",{}).get("portfolio",[]) or []
        ans=[]
        for v in portfolio:
            s=float(v.get("portfolio_score",0) or 0)
            suggested=500 if s>=80 else 100 if s>=60 else 0
            ans.append({"venture_id":v.get("venture_id"),"name":v.get("name"),
                        "portfolio_score":s,"suggested_test_budget_usd":suggested,
                        "approved_budget_usd":0,"requires_approval":True})
        return ans

    def run_cycle(self):
        ledger=self.ledger()
        rev=sum(x["amount_usd"] for x in ledger if x["type"]=="REVENUE")
        exp=sum(x["amount_usd"] for x in ledger if x["type"]=="EXPENSE")
        profit=rev-exp
        budgets=self.budgets()
        approvals=[{"approval_id":"budget-"+str(b["venture_id"]),"type":"TEST_BUDGET",
                    "name":b["name"],"amount_usd":b["suggested_test_budget_usd"],
                    "status":"REVIEW_REQUIRED"} for b in budgets if b["suggested_test_budget_usd"]>0]
        storefront=rj(self.live/"autonomous_storefront_sales_v29_live.json",{}).get("analytics",{})
        wallet=None
        for p in [self.live/"wallet_status.json",
                  self.home/"ceo_memory/crypto_treasury_wallet_registry.json",
                  self.home/"ceo_memory/crypto_treasury_ledger.json"]:
            if p.exists(): wallet=str(p); break
        state={
          "status":"autonomous_finance_treasury_ready",
          "ledger_entries":len(ledger),
          "pnl":{"revenue_usd":round(rev,2),"expenses_usd":round(exp,2),
                 "net_profit_usd":round(profit,2),
                 "net_margin_percent":round((profit/rev)*100,2) if rev else 0.0},
          "forecast":{"next_30_days":{"conservative_usd":round(rev*1.10,2),
                    "base_usd":round(rev*1.50,2),"growth_usd":round(rev*2.0,2),
                    "assumption":"Scenario math only; not a prediction."}},
          "venture_budgets":budgets,"approval_queue":approvals,
          "storefront_reconciliation":{"orders_total":storefront.get("orders_total",0),
                    "orders_paid":storefront.get("orders_paid",0),
                    "verified_revenue_usd":storefront.get("verified_revenue_usd",0)},
          "treasury_wallet_detected":bool(wallet),"treasury_wallet_source":wallet,
          "automatic_transfers_enabled":False,"automatic_spending_enabled":False,
          "automatic_tax_filing_enabled":False,"external_financial_actions_enabled":False,
          "dashboard_url":"http://127.0.0.1:8792","updated_at":now()
        }
        wj(self.rec/"executive_ledger.json",{"entries":ledger,"updated_at":now()})
        wj(self.rec/"venture_budgets.json",{"budgets":budgets,"updated_at":now()})
        wj(self.rec/"finance_approval_queue.json",{"approvals":approvals,"updated_at":now()})
        wj(self.run/"finance_treasury_state.json",state)
        wj(self.live/"autonomous_finance_treasury_v30_live.json",state)
        return state
