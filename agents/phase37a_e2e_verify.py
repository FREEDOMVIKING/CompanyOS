#!/usr/bin/env python3
import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"
DESTS=MEM/"treasury_destination_registry.json"
PROPS=MEM/"transaction_proposals.json"
OUT=MEM/"phase37a_e2e_report.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def run(args):
    p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=300)
    try:r=json.loads(p.stdout)
    except:r={"success":False,"status":"invalid_json","stdout":p.stdout[-2000:],"stderr":p.stderr[-1000:]}
    return p.returncode,r

def registered_solana_destination():
    for x in load(DESTS,{"destinations":[]}).get("destinations",[]):
        if x.get("enabled") and x.get("chain")=="solana":
            return x.get("address")
    return None

dest=registered_solana_destination()
if not dest:
    r={"success":False,"status":"no_registered_solana_destination"}
    print(json.dumps(r,indent=2))
    raise SystemExit(1)

# Create a tiny proposal only; no executor is called directly.
rc,created=run([
    sys.executable,
    "companyos/transactionproposalctl",
    "propose",
    "1",
    "0.000001",
    "SOL",
    "solana",
    dest,
    "Phase 37A end-to-end no-broadcast verification"
])

if rc!=0 or not created.get("success"):
    print(json.dumps({"success":False,"status":"proposal_creation_failed","detail":created},indent=2))
    raise SystemExit(1)

proposal=created.get("proposal") or {}
pid=proposal.get("proposal_id")

# Run Phase 37 safety controller only.
# Its broadcast_enabled flag must still be false.
rc2,result=run([sys.executable,"companyos/phase37ctl","run"])

props=load(PROPS,{"proposals":[]}).get("proposals",[])
final=next((x for x in props if x.get("proposal_id")==pid),proposal)

report={
  "generated_at":now(),
  "proposal_id":pid,
  "destination":dest,
  "proposal_status":final.get("status"),
  "phase37_result":result,
  "broadcast_attempted":False
}

OUT.write_text(json.dumps(report,indent=2))

ok = (
    proposal.get("status")=="ready_for_signing"
    and proposal.get("signing_authorized") is True
    and result.get("report",{}).get("broadcast_attempted") is False
)

print(json.dumps({
  "success":bool(ok),
  "status":"phase37a_e2e_no_broadcast_complete" if ok else "phase37a_e2e_no_broadcast_failed",
  "report":report
},indent=2))

raise SystemExit(0 if ok else 1)
