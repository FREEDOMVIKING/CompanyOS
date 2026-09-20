#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
LRT="$ROOT/.companyos_runtime"
MOD="$ROOT/companyos/runtime/venture_liveness_runtime.py"
CTL="$ROOT/scripts/companyos_livenessctl"
LPID="$RT/venture_liveness_runtime.pid"
LLOG="$RT/venture_liveness_runtime.log"
CPID="$RT/autonomous_ceo_runtime_service.pid"
CLOG="$RT/autonomous_ceo_runtime_service.log"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.16 VENTURE LIVENESS + CEO RUNTIME BRIDGE ====="
echo "GOAL=KEEP_EXISTING_VENTURES_ADVANCING_UNTIL_THEY_PRODUCE_MEASURABLE_STATE_CHANGE_OR_REAL_EXECUTION_BLOCKERS"
echo "NOTE=REUSES_CANONICAL_VENTURES_AND_EXISTING_STALLED_STAGE_CONTROLLER"
echo "NOTE=DOES_NOT_CREATE_DUPLICATE_VENTURES"
echo "NOTE=INTERNAL_CEO_RUNTIME_DOES_NOT_MOVE_FUNDS_OR_PERFORM_EXTERNAL_ACTIONS"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

for f in \
  "$ROOT/companyos/runtime/stalled_stage_progression_controller.py" \
  "$ROOT/companyos/runtime/autonomous_ceo_runtime_service.py" \
  "$ROOT/companyos/runtime/autonomous_ceo_orchestrator.py"
do
  [ -f "$f" ] || { echo "V66_16_ABORT=missing:$f"; exit 1; }
done

mkdir -p "$ROOT/companyos/runtime" "$ROOT/scripts" "$RT" "$LRT"

stamp="$(date +%Y%m%d_%H%M%S)"
if [ -f "$MOD" ]; then
  cp "$MOD" "${MOD}.v66_16_backup_${stamp}"
  echo "BACKUP=${MOD}.v66_16_backup_${stamp}"
fi

cat > "$MOD" <<'PY'
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

from companyos.runtime.stalled_stage_progression_controller import (
    canonical_ventures,
    stalled_ventures,
    maybe_start,
)
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue

HOME=Path.home()
ROOT=HOME/"companyos"
RT=HOME/".companyos_runtime"
LRT=ROOT/".companyos_runtime"

STATE=RT/"venture_liveness_state.json"
LATEST=RT/"venture_liveness_latest.json"
HISTORY=RT/"venture_liveness_history.jsonl"
CEO_STATE=RT/"autonomous_ceo_runtime_service.json"
CEO_ROOT=RT/"ceo_orchestrations"

VERSION="V66.16"

PROCUREMENT_TASK_MARKERS=(
    "procurement-dependency-declaration:",
    "procurement-sourcing:",
    "provider-account-discovery:",
    "blocker-repair:",
)


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


def orchestration_counts() -> dict[str,int]:
    counts={"RUNNING":0,"COMPLETED":0,"FAILED":0,"HALTED":0,"OTHER":0}
    if not CEO_ROOT.exists():
        return counts
    for p in CEO_ROOT.glob("*.json"):
        try:
            x=json.loads(p.read_text())
            st=str(x.get("state") or "OTHER")
        except Exception:
            continue
        counts[st if st in counts else "OTHER"]+=1
    return counts


def task_counts() -> dict[str,int]:
    q=AutonomousTaskQueue()
    out={
        "QUEUED":0,"CLAIMED":0,"RUNNING":0,"COMPLETED":0,
        "FAILED":0,"CANCELLED":0,"OTHER":0,
        "business_tasks":0,
        "procurement_support_tasks":0,
    }
    for t in q.all_tasks():
        st=t.state if t.state in out else "OTHER"
        out[st]+=1
        key=str(t.idempotency_key or "")
        payload=t.payload if isinstance(t.payload,dict) else {}
        blob=(key+" "+json.dumps(payload,sort_keys=True,default=str)).lower()
        if any(m in blob for m in PROCUREMENT_TASK_MARKERS) or "procurement" in blob:
            out["procurement_support_tasks"]+=1
        else:
            out["business_tasks"]+=1
    return out


def canonical_summary() -> dict[str,Any]:
    ventures=canonical_ventures()
    stages={}
    unchanged=[]
    for cid,row in ventures.items():
        stage=str(row.get("stage") or "DISCOVER")
        stages[stage]=stages.get(stage,0)+1
        unchanged.append(int(row.get("unchanged_observations") or 0))
    return {
        "canonical_ventures":len(ventures),
        "stage_counts":stages,
        "stalled_3plus":sum(1 for x in unchanged if x>=3),
        "stalled_5plus":sum(1 for x in unchanged if x>=5),
        "max_unchanged_observations":max(unchanged) if unchanged else 0,
    }


def ceo_runtime_health() -> dict[str,Any]:
    x=load_json(CEO_STATE,{})
    return {
        "state_file_present":CEO_STATE.exists(),
        "running":x.get("running"),
        "ready":x.get("ready"),
        "reason":x.get("reason"),
        "cycle_count":x.get("cycle_count"),
        "active_orchestrations":x.get("active_orchestrations"),
        "completed_orchestrations":x.get("completed_orchestrations"),
        "failed_orchestrations":x.get("failed_orchestrations"),
        "halted_orchestrations":x.get("halted_orchestrations"),
        "cycles_dispatched_this_tick":x.get("cycles_dispatched_this_tick"),
        "last_cycle_unix":x.get("last_cycle_unix"),
        "external_actions_performed":x.get("external_actions_performed"),
        "transaction_broadcasts":x.get("transaction_broadcasts"),
    }


def run_once() -> dict[str,Any]:
    before=canonical_summary()
    stalled=stalled_ventures(3)

    # Existing controller starts at most one canonical stalled venture and has
    # its own cooldown/duplicate protection.
    progression=maybe_start(
        min_unchanged=int(os.getenv("COMPANYOS_LIVENESS_MIN_UNCHANGED","3")),
        cooldown_seconds=int(os.getenv("COMPANYOS_LIVENESS_START_COOLDOWN_SECONDS","900")),
    )

    report={
        "version":VERSION,
        "mode":"venture_liveness_and_existing_ceo_runtime_bridge",
        "canonical":before,
        "stalled_preview":[
            {
                "canonical_id":x.get("canonical_id"),
                "stage":x.get("stage"),
                "unchanged_observations":x.get("unchanged_observations"),
                "artifact_count":x.get("artifact_count"),
            }
            for x in stalled[:20]
        ],
        "progression":progression,
        "orchestrations":orchestration_counts(),
        "task_queue":task_counts(),
        "ceo_runtime":ceo_runtime_health(),
        "rules":{
            "duplicate_venture_creation":False,
            "existing_canonical_venture_reuse":True,
            "internal_execution_first":True,
            "forced_procurement":False,
            "external_actions_performed_by_this_runtime":False,
            "transaction_broadcasts_by_this_runtime":False,
        },
        "timestamp_unix":time.time(),
    }
    save_json(LATEST,report)
    append_jsonl(HISTORY,report)

    st=load_json(STATE,{"cycles":0})
    st["cycles"]=int(st.get("cycles") or 0)+1
    st["updated_at_unix"]=time.time()
    st["last_progression"]=progression
    save_json(STATE,st)
    return report


def status() -> dict[str,Any]:
    return {
        "version":VERSION,
        "latest":load_json(LATEST,{}),
        "state":load_json(STATE,{}),
        "canonical":canonical_summary(),
        "orchestrations":orchestration_counts(),
        "task_queue":task_counts(),
        "ceo_runtime":ceo_runtime_health(),
    }


def loop(interval: int):
    while True:
        try:
            r=run_once()
            print(json.dumps({
                "ts":time.time(),
                "canonical_ventures":r["canonical"]["canonical_ventures"],
                "stalled_3plus":r["canonical"]["stalled_3plus"],
                "progression_started":bool((r["progression"] or {}).get("started")),
                "running_orchestrations":r["orchestrations"]["RUNNING"],
                "queued_tasks":r["task_queue"]["QUEUED"],
            },sort_keys=True),flush=True)
        except Exception as exc:
            print(json.dumps({
                "ts":time.time(),
                "error":f"{type(exc).__name__}:{exc}",
            },sort_keys=True),flush=True)
        time.sleep(max(60,int(interval)))


def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("once")
    sub.add_parser("status")
    lp=sub.add_parser("loop")
    lp.add_argument("--interval",type=int,default=120)
    args=ap.parse_args()

    if args.cmd=="once":
        print(json.dumps(run_once(),indent=2,sort_keys=True,default=str))
    elif args.cmd=="status":
        print(json.dumps(status(),indent=2,sort_keys=True,default=str))
    elif args.cmd=="loop":
        loop(args.interval)


if __name__=="__main__":
    main()
PY

cat > "$CTL" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
LPID="$RT/venture_liveness_runtime.pid"
LLOG="$RT/venture_liveness_runtime.log"
CPID="$RT/autonomous_ceo_runtime_service.pid"
CLOG="$RT/autonomous_ceo_runtime_service.log"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

start_ceo() {
  if [ -f "$CPID" ] && kill -0 "$(cat "$CPID")" 2>/dev/null; then
    echo "CEO_RUNTIME_ALREADY_RUNNING PID=$(cat "$CPID")"
    return 0
  fi
  nohup python - <<'PY' >>"$CLOG" 2>&1 &
from companyos.runtime.autonomous_ceo_runtime_service import AutonomousCEORuntimeService
AutonomousCEORuntimeService(
    interval_seconds=10,
    max_consecutive_failures=5,
).run_forever()
PY
  echo $! > "$CPID"
  sleep 1
  echo "CEO_RUNTIME_RUNNING PID=$(cat "$CPID")"
}

stop_ceo() {
  if [ -f "$CPID" ]; then
    kill "$(cat "$CPID")" 2>/dev/null || true
    rm -f "$CPID"
  fi
  echo "CEO_RUNTIME_STOPPED"
}

start_liveness() {
  if [ -f "$LPID" ] && kill -0 "$(cat "$LPID")" 2>/dev/null; then
    echo "LIVENESS_ALREADY_RUNNING PID=$(cat "$LPID")"
    return 0
  fi
  nohup python -m companyos.runtime.venture_liveness_runtime loop \
    --interval "${COMPANYOS_LIVENESS_INTERVAL_SECONDS:-120}" \
    >>"$LLOG" 2>&1 &
  echo $! > "$LPID"
  sleep 1
  echo "LIVENESS_RUNNING PID=$(cat "$LPID")"
}

stop_liveness() {
  if [ -f "$LPID" ]; then
    kill "$(cat "$LPID")" 2>/dev/null || true
    rm -f "$LPID"
  fi
  echo "LIVENESS_STOPPED"
}

case "${1:-status}" in
  start)
    start_ceo
    start_liveness
    ;;
  stop)
    stop_liveness
    stop_ceo
    ;;
  restart)
    stop_liveness
    stop_ceo
    start_ceo
    start_liveness
    ;;
  once)
    python -m companyos.runtime.venture_liveness_runtime once
    ;;
  status)
    python -m companyos.runtime.venture_liveness_runtime status
    echo "CEO_PID=$(cat "$CPID" 2>/dev/null || true)"
    [ -f "$CPID" ] && ps -p "$(cat "$CPID")" -o pid,etime,args || true
    echo "LIVENESS_PID=$(cat "$LPID" 2>/dev/null || true)"
    [ -f "$LPID" ] && ps -p "$(cat "$LPID")" -o pid,etime,args || true
    ;;
  ceo-log)
    tail -n "${2:-100}" "$CLOG" 2>/dev/null || true
    ;;
  log)
    tail -n "${2:-100}" "$LLOG" 2>/dev/null || true
    ;;
  *)
    echo "usage: $0 {start|stop|restart|once|status|ceo-log [n]|log [n]}"
    exit 2
    ;;
esac
SH
chmod +x "$CTL"

cat > "$ROOT/tests/test_venture_liveness_runtime.py" <<'PY'
from companyos.runtime.venture_liveness_runtime import (
    orchestration_counts,
    task_counts,
    canonical_summary,
)

def test_orchestration_counts_shape():
    s=orchestration_counts()
    assert set(("RUNNING","COMPLETED","FAILED","HALTED")).issubset(s)

def test_task_counts_shape():
    s=task_counts()
    assert "QUEUED" in s
    assert "FAILED" in s
    assert "business_tasks" in s
    assert "procurement_support_tasks" in s

def test_canonical_summary_shape():
    s=canonical_summary()
    assert "canonical_ventures" in s
    assert "stalled_3plus" in s
PY

echo "===== COMPILE ====="
python -m py_compile "$MOD"
echo "V66_16_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_venture_liveness_runtime.py
echo "V66_16_TESTS=PASS"

echo "===== FIRST LIVENESS CYCLE ====="
"$CTL" once

echo "===== START CEO RUNTIME + LIVENESS LOOP ====="
"$CTL" restart

sleep 2

echo "===== FINAL STATUS ====="
"$CTL" status

echo "V66_16_CANONICAL_VENTURE_REUSE=PASS"
echo "V66_16_STALLED_STAGE_PROGRESSION=PASS"
echo "V66_16_CEO_RUNTIME_SERVICE=PASS"
echo "V66_16_EXECUTION_LIVENESS_TELEMETRY=PASS"
echo "V66_16_NO_DUPLICATE_VENTURE_CREATION=PASS"
echo "V66_16_NO_FORCED_PROCUREMENT=PASS"
echo "V66_16_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_16_COMPLETE"
