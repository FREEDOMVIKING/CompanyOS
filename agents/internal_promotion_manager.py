#!/usr/bin/env python3
import json,shutil
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory";LAB=ROOT/"platform_lab"
TESTS=MEM/"self_test_report.json";BUILDS=MEM/"sandbox_build_report.json";OUT=MEM/"internal_promotion_report.json"
STATE=MEM/"internal_promotion_state.json";HEALTH=MEM/"internal_promotion_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    tests={x["proposal_id"]:x for x in load(TESTS,{}).get("tests",[])}
    promoted=[]
    for b in load(BUILDS,{}).get("builds",[]):
        if not tests.get(b["proposal_id"],{}).get("passed"): continue
        src=Path(b["sandbox_dir"])/"module.py"
        dst=LAB/"promoted"/f"{b['capability']}_{b['proposal_id']}.py"
        shutil.copy2(src,dst)
        promoted.append({"proposal_id":b["proposal_id"],"capability":b["capability"],"promoted_path":str(dst),"status":"promoted_internal"})
    payload={"generated_at":now(),"promotion_count":len(promoted),"promotions":promoted,
             "note":"Internal promotion only. External deployment still follows registered deployment authority."}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"promotion_count":len(promoted)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"internal_promotion_complete","report":payload}
print(json.dumps(run(),indent=2))
