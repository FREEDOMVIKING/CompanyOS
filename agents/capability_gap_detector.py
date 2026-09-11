#!/usr/bin/env python3
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"capability_gap_report.json"
STATE=MEM/"capability_gap_state.json"
HEALTH=MEM/"capability_gap_health.json"

CHECKS=[
 ("financial_execution", ["companyos/financialexecutionctl","connectors/financial_adapter.py"]),
 ("communications", ["companyos/externalactionctl","connectors/communications_adapter.py"]),
 ("publication", ["companyos/externalactionctl","connectors/publication_adapter.py"]),
 ("deployment", ["companyos/externalactionctl","connectors/deployment_adapter.py"]),
 ("hybrid_ai", ["companyos/phase25bundle1ctl","agents/specialist_runtime_adapter.py"]),
 ("multi_agent", ["companyos/phase25bundle2ctl"]),
 ("autonomous_ceo", ["companyos/phase25bundle3ctl"])
]

def now():return datetime.now(timezone.utc).isoformat()
def gid(x):return hashlib.sha256(x.encode()).hexdigest()[:18]
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    gaps=[]
    for name,paths in CHECKS:
        missing=[p for p in paths if not (ROOT/p).exists()]
        if missing:
            gaps.append({"gap_id":gid(name),"capability":name,"missing":missing,"priority":80,"status":"open"})
    payload={"generated_at":now(),"gap_count":len(gaps),"gaps":gaps}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"gap_count":len(gaps)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"capability_gap_detection_complete","report":payload}
print(json.dumps(run(),indent=2))
