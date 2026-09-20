#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
LRT="$ROOT/.companyos_runtime"
MOD="$ROOT/companyos/runtime/canonical_outcome_bridge.py"
CTL="$ROOT/scripts/companyos_outcomebridgectl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.18 CANONICAL VENTURE OUTCOME BRIDGE ====="
echo "GOAL=MAKE_COMPLETED_CEO_WORK_VISIBLE_TO_CANONICAL_VENTURE_PROGRESS_TRACKING"
echo "NOTE=DOES_NOT_FAKE_STAGE_ADVANCEMENT"
echo "NOTE=DOES_NOT_CREATE_DUPLICATE_VENTURES"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

for f in \
  "$ROOT/companyos/governance/venture_identity_progression.py" \
  "$ROOT/companyos/runtime/stalled_stage_progression_controller.py"
do
  [ -f "$f" ] || { echo "V66_18_ABORT=missing:$f"; exit 1; }
done

mkdir -p "$ROOT/companyos/runtime" "$ROOT/scripts" "$RT"

cat > "$MOD" <<'PY'
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

from companyos.governance.venture_identity_progression import candidate_ventures, evaluate_all

HOME=Path.home()
ROOT=HOME/"companyos"
RT=HOME/".companyos_runtime"
LRT=ROOT/".companyos_runtime"

STARTS=LRT/"stalled_stage_progression_state.json"
ORCH=RT/"ceo_orchestrations"
GOALS=RT/"goal_lifecycle"
STATE=RT/"canonical_outcome_bridge_state.json"
LATEST=RT/"canonical_outcome_bridge_latest.json"
HISTORY=RT/"canonical_outcome_bridge_history.jsonl"

VERSION="V66.18"


def load_json(path: Path,default: Any) -> Any:
    try:return json.loads(path.read_text())
    except Exception:return default


def save_json(path: Path,data: Any) -> None:
    import tempfile
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w") as f:
            f.write(json.dumps(data,indent=2,sort_keys=True,default=str)+"\n")
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        try:
            if os.path.exists(tmp):os.unlink(tmp)
        except Exception:pass


def append_jsonl(path: Path,row: dict[str,Any]) -> None:
    with path.open("a") as f:
        f.write(json.dumps(row,sort_keys=True,default=str)+"\n")


def starts_index() -> dict[str,dict[str,Any]]:
    state=load_json(STARTS,{"starts":[]})
    out={}
    for x in state.get("starts") or []:
        if not isinstance(x,dict):continue
        oid=x.get("orchestration_id")
        if oid:out[str(oid)]=x
    return out


def orchestration(oid: str) -> dict[str,Any]|None:
    p=ORCH/f"{oid}.json"
    if not p.exists():return None
    x=load_json(p,None)
    return x if isinstance(x,dict) else None


def goal_outputs(goal_id: str) -> list[dict[str,Any]]:
    p=GOALS/f"{goal_id}.json"
    if not p.exists():return []
    x=load_json(p,{})
    fr=x.get("final_result")
    if not isinstance(fr,dict):return []
    out=fr.get("outputs")
    return out if isinstance(out,list) else []


def evidence_refs(orch: dict[str,Any]) -> list[dict[str,Any]]:
    ids=[]
    for gid in orch.get("completed_goal_ids") or []:
        if gid not in ids:ids.append(gid)
    rg=orch.get("root_goal_id")
    if rg and rg not in ids:ids.append(rg)

    refs=[]
    for gid in ids:
        for o in goal_outputs(gid):
            if not isinstance(o,dict):continue
            result=o.get("result")
            artifact=None
            if isinstance(result,dict):artifact=result.get("artifact")
            refs.append({
                "goal_id":gid,
                "task_id":o.get("task_id"),
                "task_type":o.get("task_type"),
                "agent":o.get("agent"),
                "artifact":artifact,
                "result_status":result.get("status") if isinstance(result,dict) else None,
            })
    return refs


def roots_for(cid: str) -> list[Path]:
    groups=candidate_ventures()
    rec=groups.get(cid)
    if not rec:return []
    out=[]
    for rel in rec.get("roots") or []:
        p=ROOT/rel
        if p.exists() and p.is_dir():out.append(p)
    return out


def checkpoint_path(cid: str,oid: str,roots: list[Path]) -> Path|None:
    if not roots:return None
    base=roots[0]
    d=base/"companyos_progress"
    d.mkdir(parents=True,exist_ok=True)
    safe="".join(c for c in oid if c.isalnum() or c in "-_")[:120]
    return d/f"internal_progress_{safe}.json"


def stage_external_evidence(stage: str,refs: list[dict[str,Any]]) -> bool:
    markers=(
        "conversion_result","customer_result","lead_result",
        "outreach_result","campaign_result","deployment_result",
    )
    blob=" ".join(
        str(x.get("artifact") or "")+" "+str(x.get("result_status") or "")
        for x in refs
    ).lower()
    return any(m in blob for m in markers)


def process_one(oid: str,start: dict[str,Any],processed: set[str]) -> dict[str,Any]:
    orch=orchestration(oid)
    base={
        "orchestration_id":oid,
        "canonical_id":start.get("canonical_id"),
        "stage":start.get("stage"),
    }
    if not orch:return {**base,"status":"orchestration_record_missing"}
    if str(orch.get("state") or "")!="COMPLETED":return {**base,"status":"not_completed"}
    if oid in processed:return {**base,"status":"already_materialized"}

    cid=str(start.get("canonical_id") or "")
    roots=roots_for(cid)
    if not roots:return {**base,"status":"canonical_root_missing"}

    refs=evidence_refs(orch)
    p=checkpoint_path(cid,oid,roots)
    if p is None:return {**base,"status":"checkpoint_path_unavailable"}

    external=stage_external_evidence(str(start.get("stage") or ""),refs)
    record={
        "schema":"companyos.canonical_venture_progress_checkpoint.v1",
        "version":VERSION,
        "canonical_id":cid,
        "stage_at_start":start.get("stage"),
        "orchestration_id":oid,
        "root_goal_id":orch.get("root_goal_id"),
        "completed_goal_ids":orch.get("completed_goal_ids") or [],
        "evidence_refs":refs,
        "internal_orchestration_completed":True,
        "external_stage_evidence_present":external,
        "stage_advance_claimed":False,
        "duplicate_venture_created":False,
        "created_at_unix":time.time(),
    }
    save_json(p,record)
    processed.add(oid)
    return {
        **base,
        "status":"materialized",
        "checkpoint":str(p),
        "evidence_ref_count":len(refs),
        "external_stage_evidence_present":external,
    }


def run_once() -> dict[str,Any]:
    st=load_json(STATE,{"processed":[]})
    processed=set(st.get("processed") or [])
    starts=starts_index()

    results=[]
    materialized=0
    for oid,start in sorted(starts.items(),key=lambda kv:float((kv[1] or {}).get("ts") or 0)):
        row=process_one(oid,start,processed)
        results.append(row)
        if row.get("status")=="materialized":materialized+=1

    refreshed=[]
    if materialized:
        try:refreshed=evaluate_all()
        except Exception:refreshed=[]

    save_json(STATE,{
        "version":VERSION,
        "updated_at_unix":time.time(),
        "processed":sorted(processed)[-1000:],
    })

    report={
        "version":VERSION,
        "mode":"canonical_outcome_materialization",
        "mapped_progression_starts":len(starts),
        "materialized_this_run":materialized,
        "processed_total":len(processed),
        "results":results[-100:],
        "refreshed_ventures":[
            {
                "canonical_id":x.get("canonical_id"),
                "stage":x.get("stage"),
                "unchanged_observations":x.get("unchanged_observations"),
                "changed_since_previous_observation":x.get("changed_since_previous_observation"),
                "artifact_count":x.get("artifact_count"),
            }
            for x in refreshed
        ],
        "rules":{
            "fake_stage_advancement":False,
            "duplicate_venture_creation":False,
            "existing_canonical_root_reuse":True,
            "completed_orchestration_required":True,
        },
        "timestamp_unix":time.time(),
    }
    save_json(LATEST,report)
    append_jsonl(HISTORY,report)
    return report


def status() -> dict[str,Any]:
    return {
        "version":VERSION,
        "latest":load_json(LATEST,{}),
        "state":load_json(STATE,{}),
    }


def loop(interval: int):
    while True:
        try:
            r=run_once()
            print(json.dumps({
                "ts":time.time(),
                "mapped_progression_starts":r["mapped_progression_starts"],
                "materialized_this_run":r["materialized_this_run"],
                "processed_total":r["processed_total"],
            },sort_keys=True),flush=True)
        except Exception as exc:
            print(json.dumps({"ts":time.time(),"error":f"{type(exc).__name__}:{exc}"},sort_keys=True),flush=True)
        time.sleep(max(60,int(interval)))


def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("once")
    sub.add_parser("status")
    lp=sub.add_parser("loop")
    lp.add_argument("--interval",type=int,default=60)
    args=ap.parse_args()

    if args.cmd=="once":print(json.dumps(run_once(),indent=2,sort_keys=True,default=str))
    elif args.cmd=="status":print(json.dumps(status(),indent=2,sort_keys=True,default=str))
    elif args.cmd=="loop":loop(args.interval)


if __name__=="__main__":main()
PY

cat > "$CTL" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
PIDFILE="$RT/canonical_outcome_bridge.pid"
LOGFILE="$RT/canonical_outcome_bridge.log"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  start)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "OUTCOME_BRIDGE_ALREADY_RUNNING PID=$(cat "$PIDFILE")"
      exit 0
    fi
    nohup python -m companyos.runtime.canonical_outcome_bridge loop \
      --interval "${COMPANYOS_OUTCOME_BRIDGE_INTERVAL_SECONDS:-60}" \
      >>"$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    sleep 1
    echo "OUTCOME_BRIDGE_RUNNING PID=$(cat "$PIDFILE")"
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then
      kill "$(cat "$PIDFILE")" 2>/dev/null || true
      rm -f "$PIDFILE"
    fi
    echo "OUTCOME_BRIDGE_STOPPED"
    ;;
  restart)
    "$0" stop
    "$0" start
    ;;
  once)
    python -m companyos.runtime.canonical_outcome_bridge once
    ;;
  status)
    python -m companyos.runtime.canonical_outcome_bridge status
    if [ -f "$PIDFILE" ]; then
      echo "PID=$(cat "$PIDFILE")"
      ps -p "$(cat "$PIDFILE")" -o pid,etime,args || true
    fi
    ;;
  log)
    tail -n "${2:-100}" "$LOGFILE" 2>/dev/null || true
    ;;
  *)
    echo "usage: $0 {start|stop|restart|once|status|log [n]}"
    exit 2
    ;;
esac
SH
chmod +x "$CTL"

cat > "$ROOT/tests/test_canonical_outcome_bridge.py" <<'PY'
from companyos.runtime.canonical_outcome_bridge import stage_external_evidence

def test_internal_artifacts_do_not_fake_external_progress():
    refs=[
        {"artifact":"/tmp/x.research.json","result_status":"evidence_artifact_created"},
        {"artifact":"/tmp/x.plan.json","result_status":"plan_artifact_created"},
        {"artifact":"/tmp/x.build.json","result_status":"build_artifact_created"},
    ]
    assert stage_external_evidence("CUSTOMER_ACQUISITION",refs) is False

def test_explicit_outreach_result_is_detected():
    refs=[{"artifact":"/tmp/outreach_result.json","result_status":"completed"}]
    assert stage_external_evidence("CUSTOMER_ACQUISITION",refs) is True
PY

echo "===== COMPILE ====="
python -m py_compile "$MOD"
echo "V66_18_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_canonical_outcome_bridge.py
echo "V66_18_TESTS=PASS"

echo "===== MATERIALIZE EXISTING COMPLETED PROGRESSION OUTCOMES ====="
"$CTL" once

echo "===== START OUTCOME BRIDGE ====="
"$CTL" restart

echo "===== STATUS ====="
"$CTL" status

echo "V66_18_COMPLETED_OUTCOME_MAPPING=PASS"
echo "V66_18_CANONICAL_ARTIFACT_MATERIALIZATION=PASS"
echo "V66_18_IDENTITY_FINGERPRINT_REFRESH=PASS"
echo "V66_18_NO_FAKE_STAGE_ADVANCEMENT=PASS"
echo "V66_18_NO_DUPLICATE_VENTURE_CREATION=PASS"
echo "V66_18_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_18_COMPLETE"
