#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase35_ceo_treasury_bridge_config.json"
REQ=MEM/"ceo_treasury_requests.json"
AUDIT=MEM/"phase35_ceo_treasury_audit.jsonl"
REPORT=MEM/"phase35_ceo_treasury_report.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def audit(x):
    with AUDIT.open("a") as f:f.write(json.dumps({"at":now(),**x})+"\n")
def run_cmd(args):
    p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=300)
    try:r=json.loads(p.stdout)
    except:r={"success":False,"status":"invalid_json_output","stdout":p.stdout[-2000:],"stderr":p.stderr[-1000:]}
    return p.returncode,r

def cycle():
    cfg=load(CFG,{})
    q=load(REQ,{"requests":[]})
    pending=[x for x in q.get("requests",[]) if x.get("status")=="pending_bridge"]
    results=[]

    for x in pending[:int(cfg.get("max_ceo_requests_per_cycle",10))]:
        rid=x["request_id"]

        # Create governed Phase 32 proposal.
        rc,propres=run_cmd([
          sys.executable,"companyos/transactionproposalctl","propose",
          str(x["amount_usd"]),str(x["amount_native"]),x["asset"],x["chain"],x["destination"],x["reason"]
        ])

        if rc!=0 or not propres.get("success"):
            x["status"]="bridge_failed"
            x["bridge_error"]="proposal_creation_failed"
            row={"request_id":rid,"success":False,"status":"proposal_creation_failed","detail":propres}
            results.append(row);audit(row);continue

        proposal=propres.get("proposal") or {}
        x["proposal_id"]=proposal.get("proposal_id")
        x["proposal_status"]=proposal.get("status")

        if proposal.get("status")=="blocked":
            x["status"]="blocked_by_policy"
            row={"request_id":rid,"success":False,"status":"blocked_by_policy","proposal":proposal}
            results.append(row);audit(row);continue

        if proposal.get("status")=="pending_owner_approval":
            x["status"]="pending_owner_approval"
            row={"request_id":rid,"success":True,"status":"pending_owner_approval","proposal":proposal}
            results.append(row);audit(row);continue

        # Let Phase 34 enforce registered destination + supported live route + executor.
        rc2,execres=run_cmd([sys.executable,"companyos/autonomoustreasuryctl","run"])

        # Refresh proposal state after autonomous cycle.
        props=load(MEM/"transaction_proposals.json",{"proposals":[]}).get("proposals",[])
        updated=next((p for p in props if p.get("proposal_id")==proposal.get("proposal_id")),proposal)
        x["proposal_status"]=updated.get("status")

        if updated.get("status") in ("confirmed","broadcast","confirmation_pending"):
            x["status"]="executed"
            x["completed_at"]=now()
            row={"request_id":rid,"success":True,"status":"executed","proposal":updated,"autonomous_cycle":execres}
        else:
            x["status"]="bridge_submitted"
            row={"request_id":rid,"success":True,"status":"bridge_submitted","proposal":updated,"autonomous_cycle":execres}

        results.append(row);audit(row)

    q["updated_at"]=now();save(REQ,q)
    report={"generated_at":now(),"pending_count":len(pending),"result_count":len(results),"results":results}
    save(REPORT,report)
    return {"success":True,"status":"ceo_treasury_bridge_cycle_complete","report":report}

a=sys.argv[1] if len(sys.argv)>1 else "run"
if a=="status":
    r={"success":True,"status":"ceo_treasury_bridge_status","config":load(CFG,{}),"requests":load(REQ,{"requests":[]})}
else:
    r=cycle()
print(json.dumps(r,indent=2))
