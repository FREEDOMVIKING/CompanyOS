
import json, os, tempfile
from pathlib import Path
from datetime import datetime, timezone

def now(): return datetime.now(timezone.utc).isoformat()

def rj(p, d=None):
    if d is None: d={}
    try: return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception: return d

def wj(p, d):
    p=Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=str(p.parent), prefix=p.name+".")
    with os.fdopen(fd,"w",encoding="utf-8") as f:
        json.dump(d,f,indent=2,sort_keys=True)
    os.replace(tmp,p)

class CustomerSuccessV33:
    def __init__(self, home):
        self.home=Path(home)
        self.live=self.home/".companyos_runtime"
        self.records=self.home/"customer_success_records_v33"
        self.runtime=self.home/"companyos_runtime/autonomous_customer_success_v33_1350001_1400000"
        for p in (self.live,self.records,self.runtime): p.mkdir(parents=True,exist_ok=True)
        for name,default in [
            ("tickets.json",{"tickets":[]}),
            ("knowledge_base.json",{"articles":[]}),
            ("followups.json",{"followups":[]}),
            ("refund_review_queue.json",{"refunds":[]})
        ]:
            p=self.records/name
            if not p.exists(): wj(p,default)

    def run_cycle(self):
        tickets=rj(self.records/"tickets.json",{"tickets":[]})["tickets"]
        kb=rj(self.records/"knowledge_base.json",{"articles":[]})["articles"]
        followups=rj(self.records/"followups.json",{"followups":[]})["followups"]
        refunds=rj(self.records/"refund_review_queue.json",{"refunds":[]})["refunds"]
        orders=rj(self.home/"storefront_sales_records_v29/orders.json",{"orders":[]})["orders"]
        paid=[o for o in orders if o.get("payment_status")=="PAID_VERIFIED"]
        state={
            "status":"autonomous_customer_success_ready",
            "customers_total":len({o.get("customer_ref_hash") or o.get("order_id") for o in orders}),
            "orders_total":len(orders),
            "paid_orders":len(paid),
            "tickets_total":len(tickets),
            "tickets_open":sum(t.get("status","OPEN") not in ("RESOLVED","CLOSED") for t in tickets),
            "knowledge_articles":len(kb),
            "followups_queued":len(followups),
            "refunds_pending_review":sum(r.get("status","REVIEW_REQUIRED")=="REVIEW_REQUIRED" for r in refunds),
            "automatic_external_messages_enabled":False,
            "automatic_refunds_enabled":False,
            "automatic_credits_enabled":False,
            "dashboard_url":"http://127.0.0.1:8795",
            "updated_at":now()
        }
        wj(self.live/"autonomous_customer_success_v33_live.json",state)
        wj(self.runtime/"customer_success_state.json",state)
        return state
