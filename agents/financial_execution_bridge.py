#!/usr/bin/env python3
import json,sys,subprocess
from pathlib import Path

ROOT=Path.home()/"companyos"
def call(args):
    p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=120)
    try:return json.loads(p.stdout)
    except:return {"success":False,"raw":p.stdout,"stderr":p.stderr}

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="queue":
    amount=float(sys.argv[2]);source=sys.argv[3];dest=sys.argv[4];asset=sys.argv[5] if len(sys.argv)>5 else "USD";purpose=" ".join(sys.argv[6:])
    decision=call([sys.executable,"companyos/financialauthorityctl","evaluate",str(amount),source,dest,asset,purpose])
    d=decision.get("decision",{})
    if not d.get("allowed"):
        r={"success":True,"status":"pending_owner_approval" if d.get("requires_owner_approval") else "blocked","decision":d,"executed":False}
    else:
        payload={"amount_usd":amount,"source":source,"destination":dest,"asset":asset,"purpose":purpose}
        r=call([sys.executable,"companyos/liveexecutionctl","execute","financial",json.dumps(payload)])
else:r={"success":True,"status":"financial_execution_bridge_ready"}
print(json.dumps(r,indent=2))
