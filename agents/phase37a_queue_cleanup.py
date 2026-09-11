#!/usr/bin/env python3
import json, shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"
ARCH=MEM/"archive"
PROPS=MEM/"transaction_proposals.json"
REPORT=MEM/"phase37a_cleanup_report.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2))
    t.replace(p)

ARCH.mkdir(parents=True,exist_ok=True)
data=load(PROPS,{"proposals":[]})

backup=ARCH/f"transaction_proposals_before_phase37a_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
backup.write_text(json.dumps(data,indent=2))

archived=[]
kept=[]

for p in data.get("proposals",[]):
    dest=str(p.get("destination",""))
    reason=str(p.get("reason","")).lower()
    status=p.get("status")

    stale_demo = (
        dest=="DEMO_DESTINATION"
        or "phase 32 internal test" in reason
        or "approval threshold test" in reason
    )

    if stale_demo and status not in ("confirmed","broadcast","confirmation_pending"):
        p["archived_at"]=now()
        p["archive_reason"]="stale_demo_or_test_proposal"
        archived.append(p)
    else:
        kept.append(p)

data["proposals"]=kept
data["updated_at"]=now()
save(PROPS,data)

archive_file=ARCH/"phase37a_archived_proposals.json"
old=load(archive_file,{"proposals":[]})
old["proposals"].extend(archived)
old["updated_at"]=now()
save(archive_file,old)

report={
  "generated_at":now(),
  "backup_file":str(backup),
  "archived_count":len(archived),
  "remaining_count":len(kept),
  "archived_proposal_ids":[x.get("proposal_id") for x in archived]
}
save(REPORT,report)
print(json.dumps({"success":True,"status":"phase37a_queue_cleanup_complete","report":report},indent=2))
