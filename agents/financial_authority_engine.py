#!/usr/bin/env python3
import json, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"authority_execution_config.json"
LEDGER=MEM/"financial_authority_ledger.json"
QUEUE=MEM/"financial_execution_queue.json"
STATE=MEM/"financial_authority_state.json"
HEALTH=MEM/"financial_authority_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def today(): return datetime.now(timezone.utc).date().isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def txid(x): return hashlib.sha256(str(x).encode()).hexdigest()[:20]

def evaluate(amount_usd, source, destination, asset="USD", purpose=""):
    cfg=load(CFG,{})["financial_authority"]
    ledger=load(LEDGER,{"transactions":[]})
    spent=sum(float(x.get("amount_usd",0) or 0) for x in ledger["transactions"] if x.get("date")==today() and x.get("status")=="executed")
    reasons=[]
    requires=False
    if amount_usd > float(cfg["single_transaction_auto_approval_limit_usd"]):
        requires=True;reasons.append("single_transaction_limit")
    if spent + amount_usd > float(cfg["daily_total_limit_usd"]):
        requires=True;reasons.append("daily_total_limit")
    if cfg.get("allowed_accounts") and destination not in cfg["allowed_accounts"]:
        requires=True;reasons.append("destination_not_preapproved")
    if destination in cfg.get("blocked_accounts",[]):
        return {"allowed":False,"requires_owner_approval":False,"reason":["blocked_destination"]}
    if asset not in cfg.get("allowed_asset_classes",[]):
        requires=True;reasons.append("asset_not_preapproved")
    return {
      "allowed":not requires,
      "requires_owner_approval":requires,
      "reasons":reasons,
      "daily_spent_usd":spent,
      "daily_remaining_usd":max(0,float(cfg["daily_total_limit_usd"])-spent),
      "single_auto_limit_usd":cfg["single_transaction_auto_approval_limit_usd"]
    }

def queue(amount_usd,source,destination,asset,purpose):
    decision=evaluate(amount_usd,source,destination,asset,purpose)
    q=load(QUEUE,{"items":[]})
    item={
      "transaction_id":txid(f"{now()}|{source}|{destination}|{amount_usd}"),
      "amount_usd":amount_usd,"source":source,"destination":destination,"asset":asset,"purpose":purpose,
      "authority_decision":decision,
      "status":"ready_for_connector_execution" if decision["allowed"] else ("pending_owner_approval" if decision["requires_owner_approval"] else "blocked"),
      "created_at":now()
    }
    q["items"].append(item);save(QUEUE,q)
    save(STATE,{"last_evaluated_at":now(),"queued_count":len(q["items"])})
    save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return item

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="evaluate":
    r={"success":True,"decision":evaluate(float(sys.argv[2]),sys.argv[3],sys.argv[4],sys.argv[5] if len(sys.argv)>5 else "USD"," ".join(sys.argv[6:]) if len(sys.argv)>6 else "")}
elif a=="queue":
    item=queue(float(sys.argv[2]),sys.argv[3],sys.argv[4],sys.argv[5] if len(sys.argv)>5 else "USD"," ".join(sys.argv[6:]) if len(sys.argv)>6 else "")
    r={"success":True,"status":"financial_action_queued","item":item}
else:
    r={"success":True,"status":"financial_authority_status","state":load(STATE,{}),"queue":load(QUEUE,{"items":[]}),"ledger":load(LEDGER,{"transactions":[]})}
print(json.dumps(r,indent=2))
