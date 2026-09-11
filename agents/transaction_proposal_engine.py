#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
CFG=MEM/"phase32_transaction_policy_config.json"
BAL=MEM/"multi_asset_treasury_balances.json"
QUEUE=MEM/"transaction_proposals.json"
LEDGER=MEM/"crypto_treasury_ledger.json"

def now():return datetime.now(timezone.utc).isoformat()
def today():return datetime.now(timezone.utc).date().isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):p.write_text(json.dumps(d,indent=2))
def pid(seed):return hashlib.sha256(seed.encode()).hexdigest()[:22]

def find_balance(chain,asset):
    for w in load(BAL,{}).get("balances",[]):
        if w.get("chain")==chain:
            return (w.get("assets") or {}).get(asset), w.get("address")
    return None,None

def spent_today():
    total=0
    for x in load(LEDGER,{"transactions":[]}).get("transactions",[]):
        if x.get("date")==today() and x.get("direction")=="outgoing" and x.get("status") in ("broadcast","confirmed"):
            try: total += float(x.get("amount_usd",0) or 0)
            except: pass
    return total

def propose(amount_usd,amount_native,asset,chain,destination,reason):
    cfg=load(CFG,{})
    reasons=[]
    routes=cfg.get("supported_routes",{})
    if asset not in routes.get(chain,[]): reasons.append("asset_network_mismatch")
    if cfg.get("require_reason") and not reason.strip(): reasons.append("missing_reason")
    bal,source=find_balance(chain,asset)
    if cfg.get("require_balance_check") and bal is not None and float(amount_native)>float(bal): reasons.append("insufficient_balance")
    daily=spent_today()
    requires_approval=False
    if amount_usd>float(cfg["single_transaction_auto_limit_usd"]):
        requires_approval=True;reasons.append("single_transaction_limit")
    if daily+amount_usd>float(cfg["daily_total_limit_usd"]):
        requires_approval=True;reasons.append("daily_total_limit")
    blocked=any(x in reasons for x in ("asset_network_mismatch","missing_reason","insufficient_balance"))
    status="blocked" if blocked else ("pending_owner_approval" if requires_approval else "ready_for_signing")
    item={
      "proposal_id":pid(f"{now()}|{chain}|{asset}|{destination}|{amount_native}"),
      "created_at":now(),"date":today(),
      "chain":chain,"asset":asset,
      "source":source,"destination":destination,
      "amount_native":amount_native,"amount_usd":amount_usd,
      "reason":reason,"daily_spent_before_usd":daily,
      "policy_reasons":reasons,
      "requires_owner_approval":requires_approval,
      "status":status,
      "signing_authorized":status=="ready_for_signing",
      "broadcast_authorized":False
    }
    q=load(QUEUE,{"proposals":[]});q["proposals"].append(item);q["updated_at"]=now();save(QUEUE,q)
    return item

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="propose":
    item=propose(float(sys.argv[2]),float(sys.argv[3]),sys.argv[4],sys.argv[5],sys.argv[6]," ".join(sys.argv[7:]))
    r={"success":True,"status":"transaction_proposal_created","proposal":item}
else:
    r={"success":True,"status":"transaction_proposal_status","queue":load(QUEUE,{"proposals":[]})}
print(json.dumps(r,indent=2))
