#!/usr/bin/env python3
import json,sys,subprocess,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"; CONN=ROOT/"connectors"
LEDGER=MEM/"crypto_treasury_ledger.json"; QUEUE=MEM/"crypto_treasury_execution_queue.json"

def now():return datetime.now(timezone.utc).isoformat()
def today():return datetime.now(timezone.utc).date().isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):p.write_text(json.dumps(d,indent=2))
def tid(seed):return hashlib.sha256(seed.encode()).hexdigest()[:20]

def policy(amount_usd,asset,chain,destination):
    p=subprocess.run([sys.executable,"companyos/treasurypolicyctl",str(amount_usd),asset,chain,destination],
                     cwd=ROOT,text=True,capture_output=True,timeout=60)
    try:return json.loads(p.stdout)
    except:return {"allowed_for_auto_sign":False,"blocked":True,"reasons":["policy_error"]}

def queue_transfer(amount_usd,amount_native,asset,chain,source,destination,purpose):
    decision=policy(amount_usd,asset,chain,destination)
    q=load(QUEUE,{"items":[]})
    item={
      "transaction_id":tid(f"{now()}|{chain}|{source}|{destination}|{amount_native}|{asset}"),
      "date":today(),
      "amount_usd":amount_usd,
      "amount_native":amount_native,
      "asset":asset,
      "chain":chain,
      "source":source,
      "destination":destination,
      "purpose":purpose,
      "policy":decision,
      "status":"blocked" if decision.get("blocked") else ("ready_for_auto_sign" if decision.get("allowed_for_auto_sign") else "pending_owner_approval"),
      "created_at":now()
    }
    q["items"].append(item);save(QUEUE,q)
    return item

def execute(txid_value):
    q=load(QUEUE,{"items":[]})
    item=next((x for x in q["items"] if x.get("transaction_id")==txid_value),None)
    if not item:return {"success":False,"status":"transaction_not_found"}
    if item.get("status")!="ready_for_auto_sign":
        return {"success":False,"status":"not_authorized_for_auto_sign","item":item}
    adapter=CONN/f"{item['chain']}_treasury_adapter.py"
    if not adapter.exists():return {"success":False,"status":"adapter_missing","chain":item["chain"]}
    p=subprocess.run([sys.executable,str(adapter),"send",json.dumps(item)],cwd=ROOT,text=True,capture_output=True,timeout=300)
    if p.returncode==0:
        item["status"]="broadcast";item["broadcast_at"]=now()
        ledger=load(LEDGER,{"transactions":[]});ledger["transactions"].append(item);save(LEDGER,ledger);save(QUEUE,q)
    return {"success":p.returncode==0,"status":"broadcast" if p.returncode==0 else "send_failed",
            "stdout":p.stdout[-2500:],"stderr":p.stderr[-1000:],"item":item}

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="queue":
    item=queue_transfer(float(sys.argv[2]),float(sys.argv[3]),sys.argv[4],sys.argv[5],sys.argv[6],sys.argv[7]," ".join(sys.argv[8:]))
    r={"success":True,"status":"transfer_queued","item":item}
elif a=="execute":
    r=execute(sys.argv[2])
else:
    r={"success":True,"status":"treasury_transfer_router_ready","queue":load(QUEUE,{"items":[]})}
print(json.dumps(r,indent=2))
