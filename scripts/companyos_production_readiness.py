#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
import json, sys, time
from pathlib import Path

ROOT = Path.home() / "companyos"
RT = ROOT / ".companyos_runtime"
OPS = RT / "operations"
REPORTS = RT / "build_reports"
RELEASES = RT / "releases"
OUT = RT / "production_readiness"
STATE = RT / "production_readiness_state.json"

OUT.mkdir(parents=True, exist_ok=True)

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n")
    t.replace(p)

def assess():
    results=[]
    vids=set()
    for p in REPORTS.glob("*.json"):
        vids.add(p.stem)
    for p in OPS.glob("*.json"):
        vids.add(p.stem)

    for vid in sorted(vids):
        build=load(REPORTS/f"{vid}.json",{})
        ops=load(OPS/f"{vid}.json",{})
        rel=load(RELEASES/f"{vid}-latest.json",{})

        checks={
            "build_ok": bool(build.get("build_ok")),
            "qa_passed": build.get("qa_status")=="passed",
            "release_packaged": bool(rel.get("archive")),
            "deployment_handoff_ready": bool(rel.get("ready_for_deployment_handoff")),
            "no_active_rollback_recommendation": not bool(ops.get("rollback_recommended")),
        }

        score=sum(1 for v in checks.values() if v)
        ready_internal = score >= 4 and checks["build_ok"] and checks["qa_passed"]

        rec={
            "venture_id":vid,
            "assessed_at":time.time(),
            "checks":checks,
            "readiness_score":score,
            "readiness_max":len(checks),
            "ready_for_production_promotion":ready_internal,
            "external_launch_authorized":False,
            "financial_commitment_authorized":False,
            "requires_existing_external_action_gate":True,
        }
        save(OUT/f"{vid}.json",rec)
        results.append(rec)

    out={
        "ok":True,
        "assessed_at":time.time(),
        "ventures_assessed":len(results),
        "ready_for_promotion":sum(1 for x in results if x["ready_for_production_promotion"]),
        "results":results
    }
    save(STATE,out)
    return out

cmd=sys.argv[1] if len(sys.argv)>1 else "status"
print(json.dumps(assess() if cmd=="assess" else load(STATE,{"ok":True,"status":"not_run"}),indent=2))
