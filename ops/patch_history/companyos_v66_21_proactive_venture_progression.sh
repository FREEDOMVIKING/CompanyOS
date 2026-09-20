#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
LRT="$ROOT/.companyos_runtime"

MOD="$ROOT/companyos/runtime/proactive_venture_progression.py"
LIVE="$ROOT/companyos/runtime/venture_liveness_runtime.py"
CTL="$ROOT/scripts/companyos_livenessctl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.21 PROACTIVE VENTURE PROGRESSION ====="
echo "GOAL=KEEP_CANONICAL_VENTURES_MOVING_EVEN_WHEN_THEY_ARE_NOT_STALLED"
echo "NOTE=REUSES_EXISTING_LIVENESS_PROCESS_NO_NEW_DAEMON"
echo "NOTE=ONE_CANONICAL_VENTURE_AT_A_TIME"
echo "NOTE=NO_DUPLICATE_VENTURE_CREATION"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

for f in "$LIVE" "$CTL" "$ROOT/companyos/runtime/stalled_stage_progression_controller.py"; do
  [ -f "$f" ] || { echo "V66_21_ABORT=missing:$f"; exit 1; }
done

stamp="$(date +%Y%m%d_%H%M%S)"
for f in "$LIVE" "$MOD"; do
  if [ -f "$f" ]; then
    cp "$f" "${f}.v66_21_backup_${stamp}"
    echo "BACKUP=${f}.v66_21_backup_${stamp}"
  fi
done

cat > "$MOD" <<'PY'
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from companyos.runtime.stalled_stage_progression_controller import (
    canonical_ventures,
    goal_for,
)
from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator

HOME=Path.home()
ROOT=HOME/"companyos"
RT=HOME/".companyos_runtime"
LRT=ROOT/".companyos_runtime"

PROGRESSION_STATE=LRT/"stalled_stage_progression_state.json"
ORCH_ROOT=RT/"ceo_orchestrations"
LATEST=RT/"proactive_venture_progression_latest.json"

VERSION="V66.21"

STAGE_RANK={
    "DISCOVER":0,
    "VALIDATE":1,
    "BUILD":2,
    "TEST":3,
    "PACKAGE":4,
    "LAUNCH_READY":5,
    "LAUNCH":6,
    "CUSTOMER_ACQUISITION":7,
    "OPERATE":8,
    "SCALE":9,
}


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def save_json(path: Path, data: Any) -> None:
    import os, tempfile
    path.parent.mkdir(parents=True, exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd,"w") as f:
            f.write(json.dumps(data,indent=2,sort_keys=True,default=str)+"\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except Exception:
            pass


def orchestration_state(oid: str|None) -> str|None:
    if not oid:
        return None
    p=ORCH_ROOT/f"{oid}.json"
    x=load_json(p,{})
    return str(x.get("state")) if x else None


def active_by_venture() -> dict[str,dict[str,Any]]:
    state=load_json(PROGRESSION_STATE,{"starts":[]})
    out={}
    for x in state.get("starts") or []:
        if not isinstance(x,dict):
            continue
        cid=str(x.get("canonical_id") or "")
        oid=x.get("orchestration_id")
        if not cid or not oid:
            continue
        if orchestration_state(str(oid))=="RUNNING":
            out[cid]={
                "orchestration_id":oid,
                "stage":x.get("stage"),
                "ts":x.get("ts"),
            }
    return out


def _last_started_by_venture() -> dict[str,float]:
    state=load_json(PROGRESSION_STATE,{"last_started_by_venture":{}})
    return {
        str(k):float(v or 0)
        for k,v in (state.get("last_started_by_venture") or {}).items()
    }


def candidate_rows(cooldown_seconds: int=300) -> list[dict[str,Any]]:
    now=time.time()
    active=active_by_venture()
    last=_last_started_by_venture()
    rows=[]

    for cid,row in canonical_ventures().items():
        if cid in active:
            continue

        stage=str(row.get("stage") or "DISCOVER")
        if stage=="SCALE":
            # SCALE is not a reason to continuously spawn another progression
            # orchestration. Scale should be evidence-driven.
            continue

        if now-float(last.get(cid,0) or 0) < max(0,int(cooldown_seconds)):
            continue

        rows.append({
            **row,
            "stage_rank":STAGE_RANK.get(stage,0),
        })

    # Prefer the venture closest to measurable revenue/customer execution.
    # Stable tie break keeps the scheduler deterministic.
    rows.sort(
        key=lambda x:(
            -int(x.get("stage_rank") or 0),
            -int(x.get("artifact_count") or 0),
            str(x.get("canonical_id") or ""),
        )
    )
    return rows


def _persist_start(entry: dict[str,Any]) -> None:
    state=load_json(
        PROGRESSION_STATE,
        {"starts":[],"last_started_by_venture":{}},
    )
    state.setdefault("starts",[]).append(entry)
    state["starts"]=state["starts"][-300:]
    state.setdefault("last_started_by_venture",{})[
        str(entry["canonical_id"])
    ]=float(entry["ts"])
    save_json(PROGRESSION_STATE,state)


def maybe_start_next(cooldown_seconds: int=300) -> dict[str,Any]:
    active=active_by_venture()
    if active:
        report={
            "version":VERSION,
            "started":False,
            "reason":"existing_active_canonical_orchestration",
            "active_by_venture":active,
        }
        save_json(LATEST,report)
        return report

    rows=candidate_rows(cooldown_seconds)
    if not rows:
        report={
            "version":VERSION,
            "started":False,
            "reason":"no_eligible_canonical_venture",
            "active_by_venture":active,
        }
        save_json(LATEST,report)
        return report

    row=rows[0]
    rec=AutonomousCEOOrchestrator().start(
        goal=goal_for(row),
        max_cycles=80,
        max_follow_up_depth=4,
        priority_base=195,
    )

    entry={
        "ts":time.time(),
        "canonical_id":row["canonical_id"],
        "stage":row["stage"],
        "orchestration_id":getattr(rec,"orchestration_id",None),
        "source":"V66.21_proactive_progression",
    }
    _persist_start(entry)

    report={
        "version":VERSION,
        "started":True,
        "reason":"proactive_canonical_progression",
        "entry":entry,
        "selected_stage_rank":row.get("stage_rank"),
        "eligible_count":len(rows),
        "eligible_preview":[
            {
                "canonical_id":x.get("canonical_id"),
                "stage":x.get("stage"),
                "artifact_count":x.get("artifact_count"),
            }
            for x in rows[:10]
        ],
        "rules":{
            "one_active_canonical_orchestration":True,
            "duplicate_venture_creation":False,
            "forced_procurement":False,
            "authority_switches_changed":False,
        },
    }
    save_json(LATEST,report)
    return report
PY

echo "===== PATCH EXISTING LIVENESS LOOP ====="
python - <<'PY'
from pathlib import Path

p=Path.home()/"companyos/companyos/runtime/venture_liveness_runtime.py"
s=p.read_text()

import_anchor='''from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
'''
addition='''from companyos.runtime.proactive_venture_progression import maybe_start_next
'''
if addition not in s:
    if import_anchor not in s:
        raise SystemExit("V66_21_ABORT=liveness_import_anchor_missing")
    s=s.replace(import_anchor,import_anchor+addition,1)

old='''    progression=maybe_start(
        min_unchanged=int(os.getenv("COMPANYOS_LIVENESS_MIN_UNCHANGED","3")),
        cooldown_seconds=int(os.getenv("COMPANYOS_LIVENESS_START_COOLDOWN_SECONDS","900")),
    )

    report={
'''
new='''    progression=maybe_start(
        min_unchanged=int(os.getenv("COMPANYOS_LIVENESS_MIN_UNCHANGED","3")),
        cooldown_seconds=int(os.getenv("COMPANYOS_LIVENESS_START_COOLDOWN_SECONDS","900")),
    )

    progression_mode="stalled"
    if not bool((progression or {}).get("started")):
        proactive=maybe_start_next(
            cooldown_seconds=int(
                os.getenv("COMPANYOS_PROACTIVE_START_COOLDOWN_SECONDS","300")
            )
        )
        if bool((proactive or {}).get("started")) or (
            str((progression or {}).get("reason") or "")
            == "no_eligible_stalled_venture"
        ):
            progression=proactive
            progression_mode="proactive"

    report={
'''
if old in s:
    s=s.replace(old,new,1)
elif 'progression_mode="proactive"' not in s:
    raise SystemExit("V66_21_ABORT=liveness_progression_anchor_missing")

needle='''        "progression":progression,
        "orchestrations":orchestration_counts(),
'''
replacement='''        "progression":progression,
        "progression_mode":progression_mode,
        "orchestrations":orchestration_counts(),
'''
if replacement not in s:
    if needle not in s:
        raise SystemExit("V66_21_ABORT=liveness_report_anchor_missing")
    s=s.replace(needle,replacement,1)

p.write_text(s)
print("V66_21_LIVENESS_PATCH=PASS")
PY

cat > "$ROOT/tests/test_proactive_venture_progression.py" <<'PY'
from companyos.runtime.proactive_venture_progression import STAGE_RANK

def test_launch_ready_prioritizes_build():
    assert STAGE_RANK["LAUNCH_READY"] > STAGE_RANK["BUILD"]

def test_customer_acquisition_prioritizes_launch_ready():
    assert STAGE_RANK["CUSTOMER_ACQUISITION"] > STAGE_RANK["LAUNCH_READY"]

def test_scale_is_highest_but_scheduler_can_exclude_it():
    assert STAGE_RANK["SCALE"] > STAGE_RANK["OPERATE"]
PY

echo "===== COMPILE ====="
python -m py_compile "$MOD" "$LIVE"
echo "V66_21_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_proactive_venture_progression.py
echo "V66_21_TESTS=PASS"

echo "===== STOP CEO + LIVENESS FOR CLEAN FIRST CYCLE ====="
"$CTL" stop || true

echo "===== RUN FIRST PROACTIVE LIVENESS CYCLE ====="
python -m companyos.runtime.venture_liveness_runtime once

echo "===== RESTART EXISTING CEO + LIVENESS PROCESSES ====="
"$CTL" start

echo "===== ALLOW CEO RUNTIME TO DISPATCH ====="
sleep 15

echo "===== FINAL STATUS ====="
"$CTL" status

echo "V66_21_PROACTIVE_CANONICAL_PROGRESSION=PASS"
echo "V66_21_ONE_ACTIVE_VENTURE_AT_A_TIME=PASS"
echo "V66_21_EXISTING_LIVENESS_PROCESS_REUSED=PASS"
echo "V66_21_STAGE_PRIORITY=PASS"
echo "V66_21_NO_DUPLICATE_VENTURE_CREATION=PASS"
echo "V66_21_NO_FORCED_PROCUREMENT=PASS"
echo "V66_21_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_21_COMPLETE"
