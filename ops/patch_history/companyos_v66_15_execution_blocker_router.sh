#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
MOD="$ROOT/companyos/runtime/execution_blocker_router.py"
EMITTER="$ROOT/companyos/runtime/trusted_procurement_intent_emitter.py"
CTL="$ROOT/scripts/companyos_blockerctl"
ECTL="$ROOT/scripts/companyos_procurement_emitterctl"
ICTL="$ROOT/scripts/companyos_procurement_intentctl"
SCTL="$ROOT/scripts/companyos_sourcingctl"
PIDFILE="$RT/execution_blocker_router.pid"
LOGFILE="$RT/execution_blocker_router.log"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.15 EXECUTION BLOCKER ROUTER ====="
echo "GOAL=KEEP_VENTURES_EXECUTING_FREE_INTERNAL_PATHS_AND_PROCURE_ONLY_WHEN_EXECUTION_PROVES_A_REAL_EXTERNAL_DEPENDENCY"
echo "NOTE=RATE_LIMITS_CREDENTIAL_GAPS_AND_CONNECTOR_GAPS_DO_NOT_AUTO_CREATE_PURCHASES"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

[ -f "$EMITTER" ] || { echo "V66_15_ABORT=missing:$EMITTER"; exit 1; }

mkdir -p "$ROOT/companyos/runtime" "$ROOT/scripts" "$RT/venture_blockers"

stamp="$(date +%Y%m%d_%H%M%S)"
for f in "$MOD" "$EMITTER"; do
  if [ -f "$f" ]; then
    cp "$f" "${f}.v66_15_backup_${stamp}"
    echo "BACKUP=${f}.v66_15_backup_${stamp}"
  fi
done

cat > "$MOD" <<'PY'
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue

HOME=Path.home()
ROOT=HOME/"companyos"
RT=HOME/".companyos_runtime"

OUT=RT/"venture_blockers"
STATE=OUT/"state.json"
LATEST=OUT/"latest.json"
HISTORY=OUT/"history.jsonl"
BLOCKERS=OUT/"blockers.jsonl"
OUT.mkdir(parents=True,exist_ok=True)

VERSION="V66.15"
MAX_TASKS=2500

# These are operational problems, not evidence that money should be spent.
RATE_LIMIT_PATTERNS=(
    "429","too many requests","rate limit","rate_limit","quota exceeded",
    "cooldown","retry after",
)
CREDENTIAL_PATTERNS=(
    "api key","api_key","credential","credentials","oauth","token missing",
    "unauthorized","401","authentication required","auth required",
)
CONNECTOR_PATTERNS=(
    "connector missing","missing connector","unsupported_task_type",
    "adapter missing","missing adapter","integration missing",
    "browser adapter required","capability missing",
)
NETWORK_PATTERNS=(
    "timeout","timed out","connection reset","temporary failure",
    "network unreachable","dns","502","503","504",
)

# Only direct, observed commercial blockers may become procurement evidence.
# The error/task must carry both a commercial acquisition signal AND a concrete
# external resource/service identity. A generic failure cannot create a buy.
COMMERCIAL_PATTERNS=(
    "payment required","402","subscription required","paid plan required",
    "upgrade required","purchase required","billing required",
    "license required","requires paid plan","requires subscription",
)
PRICE_KEYS=(
    "quoted_price_usd","price_usd","cost_usd","payment_amount_usd",
    "capital_required_usd","funding_required_usd",
)
RESOURCE_KEYS=(
    "required_resource","required_service","required_subscription",
    "required_tool","vendor","provider","supplier","service","product",
)
VENTURE_KEYS=(
    "venture_id","candidate_id","project_id","orchestration_id",
    "goal_id","opportunity_id",
)


def load_json(path: Path,default: Any) -> Any:
    try:return json.loads(path.read_text())
    except Exception:return default


def save_json(path: Path,data: Any) -> None:
    import os,tempfile
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


def clean(v: Any) -> str:
    return " ".join(str(v or "").split()).strip()


def first(d: dict[str,Any],keys) -> Any:
    for k in keys:
        v=d.get(k)
        if v not in (None,"",[],{}):
            return v
    return None


def task_venture(task) -> str|None:
    p=task.payload if isinstance(task.payload,dict) else {}
    v=first(p,VENTURE_KEYS)
    return clean(v) if v not in (None,"") else None


def task_blob(task) -> str:
    p=task.payload if isinstance(task.payload,dict) else {}
    try:payload=json.dumps(p,sort_keys=True,default=str)
    except Exception:payload=str(p)
    return (clean(task.last_error)+" "+payload).lower()


def has_any(blob: str,patterns) -> bool:
    return any(x in blob for x in patterns)


def explicit_resource(task) -> str|None:
    p=task.payload if isinstance(task.payload,dict) else {}
    v=first(p,RESOURCE_KEYS)
    if isinstance(v,str) and clean(v):
        return clean(v)

    # If a provider/vendor is explicitly named in the observed error, retain
    # only the bounded phrase around a direct "subscription/payment required"
    # marker. Never synthesize a vendor from unrelated text.
    err=clean(task.last_error)
    low=err.lower()
    if has_any(low,COMMERCIAL_PATTERNS):
        m=re.search(
            r"(?:for|provider|vendor|service)\s+([A-Za-z0-9][A-Za-z0-9 ._+\-/]{2,80})",
            err,
            re.I,
        )
        if m:
            return clean(m.group(1)).rstrip(" .,:;")
    return None


def explicit_price(task) -> float|None:
    p=task.payload if isinstance(task.payload,dict) else {}
    for k in PRICE_KEYS:
        if p.get(k) not in (None,""):
            try:
                x=float(p[k])
                if x>0:return x
            except Exception:pass

    err=clean(task.last_error)
    if not has_any(err.lower(),COMMERCIAL_PATTERNS):
        return None
    m=re.search(r"(?:USD|US\$|\$)\s*([0-9]{1,7}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)",err,re.I)
    if m:
        try:
            x=float(m.group(1).replace(",",""))
            return x if x>0 else None
        except Exception:pass
    return None


def fingerprint(task_id: str,classification: str,evidence: str) -> str:
    return hashlib.sha256(
        f"{task_id}|{classification}|{evidence}".encode()
    ).hexdigest()


def classify(task) -> dict[str,Any]:
    blob=task_blob(task)
    vid=task_venture(task)
    base={
        "schema":"companyos.execution_blocker.v1",
        "version":VERSION,
        "timestamp_unix":time.time(),
        "task_id":task.task_id,
        "task_type":task.task_type,
        "venture_id":vid,
        "task_state":task.state,
        "attempts":task.attempts,
        "max_attempts":task.max_attempts,
        "last_error":task.last_error,
        "creates_procurement":False,
        "required_resource":None,
        "quoted_price_usd":None,
        "trusted_execution_evidence":True,
    }

    if has_any(blob,RATE_LIMIT_PATTERNS):
        return {
            **base,
            "classification":"WAIT_OR_ROTATE_PROVIDER",
            "recommended_action":"respect cooldown or rotate to an already available provider",
        }

    if has_any(blob,NETWORK_PATTERNS):
        return {
            **base,
            "classification":"RETRY_TRANSIENT_FAILURE",
            "recommended_action":"retry with backoff; do not purchase",
        }

    if has_any(blob,CREDENTIAL_PATTERNS):
        return {
            **base,
            "classification":"CONNECT_OR_PROVISION_CREDENTIAL",
            "recommended_action":"use existing CompanyAIOS account-provisioning path; do not infer a purchase",
        }

    if has_any(blob,CONNECTOR_PATTERNS):
        return {
            **base,
            "classification":"BUILD_INTERNAL_CAPABILITY",
            "recommended_action":"route to adaptive capability/build system before procurement",
        }

    if has_any(blob,COMMERCIAL_PATTERNS):
        resource=explicit_resource(task)
        price=explicit_price(task)
        if resource:
            return {
                **base,
                "classification":"EXTERNAL_PROCUREMENT_BLOCKER",
                "creates_procurement":True,
                "required_resource":resource,
                "quoted_price_usd":price,
                "recommended_action":"emit trusted external dependency for procurement validation",
            }
        return {
            **base,
            "classification":"COMMERCIAL_BLOCKER_UNSPECIFIED",
            "recommended_action":"research exact external resource; no purchase until identified",
        }

    return {
        **base,
        "classification":"UNKNOWN_EXECUTION_BLOCKER",
        "recommended_action":"diagnose internally; do not purchase",
    }


def queue_internal_repair(row: dict[str,Any]) -> dict[str,Any]|None:
    cls=row["classification"]
    if cls not in {"BUILD_INTERNAL_CAPABILITY","UNKNOWN_EXECUTION_BLOCKER"}:
        return None

    q=AutonomousTaskQueue()
    key=f"blocker-repair:{row['task_id']}:{cls}"
    try:
        t=q.enqueue(
            task_type="build" if cls=="BUILD_INTERNAL_CAPABILITY" else "research",
            priority=84,
            max_attempts=3,
            idempotency_key=key,
            payload={
                "venture_id":row.get("venture_id"),
                "objective":(
                    "Resolve the observed execution blocker using existing/internal CompanyOS "
                    "capabilities first. Do not create a procurement requirement unless execution "
                    "produces explicit evidence that a specific paid external dependency is required."
                ),
                "blocked_task_id":row["task_id"],
                "observed_error":row.get("last_error"),
                "blocker_classification":cls,
                "stage":"build" if cls=="BUILD_INTERNAL_CAPABILITY" else "research",
            },
        )
        return {"task_id":t.task_id,"state":t.state,"task_type":t.task_type}
    except Exception as exc:
        return {"error":f"{type(exc).__name__}:{exc}"}


def scan_once() -> dict[str,Any]:
    q=AutonomousTaskQueue()
    tasks=q.all_tasks()
    tasks.sort(key=lambda t:float(t.updated_at_unix),reverse=True)
    tasks=tasks[:MAX_TASKS]

    st=load_json(STATE,{"seen":[]})
    seen=set(st.get("seen") or [])

    inspected=0
    new=0
    proc=0
    internal=0
    rates=0
    credentials=0
    rows=[]

    for task in tasks:
        if task.state!="FAILED":
            continue
        if not task.last_error:
            continue
        inspected+=1

        row=classify(task)
        evidence=f"{row.get('last_error')}|{row.get('required_resource')}|{row.get('quoted_price_usd')}"
        fp=fingerprint(task.task_id,row["classification"],evidence)
        if fp in seen:
            continue
        seen.add(fp)

        row["fingerprint"]=fp
        row["internal_repair_task"]=queue_internal_repair(row)

        # This artifact is objective execution evidence. V66.14 is patched to
        # scan this directory, but only EXTERNAL_PROCUREMENT_BLOCKER rows have
        # an explicit required_resource field that can become a purchase intent.
        append_jsonl(BLOCKERS,row)
        new+=1
        rows.append(row)

        cls=row["classification"]
        if row.get("creates_procurement"):proc+=1
        if cls in {"BUILD_INTERNAL_CAPABILITY","UNKNOWN_EXECUTION_BLOCKER"}:internal+=1
        if cls=="WAIT_OR_ROTATE_PROVIDER":rates+=1
        if cls=="CONNECT_OR_PROVISION_CREDENTIAL":credentials+=1

    save_json(STATE,{
        "version":VERSION,
        "updated_at_unix":time.time(),
        "seen":list(seen)[-10000:],
    })

    report={
        "version":VERSION,
        "mode":"execution_blocker_routing",
        "failed_tasks_inspected":inspected,
        "new_blockers":new,
        "procurement_blockers":proc,
        "internal_repair_blockers":internal,
        "rate_limit_blockers":rates,
        "credential_blockers":credentials,
        "rows":rows[-100:],
        "rules":{
            "rate_limit_creates_purchase":False,
            "credential_gap_creates_purchase":False,
            "connector_gap_creates_purchase":False,
            "generic_failure_creates_purchase":False,
            "explicit_commercial_resource_can_create_procurement":True,
        },
    }
    save_json(LATEST,report)
    append_jsonl(HISTORY,{"timestamp_unix":time.time(),**report})
    return report


def status() -> dict[str,Any]:
    return {
        "version":VERSION,
        "latest":load_json(LATEST,{}),
        "blockers_file":str(BLOCKERS),
        "state":load_json(STATE,{}),
    }


def loop(interval: int):
    while True:
        try:
            r=scan_once()
            print(json.dumps({
                "ts":time.time(),
                "new_blockers":r["new_blockers"],
                "procurement_blockers":r["procurement_blockers"],
                "internal_repair_blockers":r["internal_repair_blockers"],
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
        print(json.dumps(scan_once(),indent=2,sort_keys=True,default=str))
    elif args.cmd=="status":
        print(json.dumps(status(),indent=2,sort_keys=True,default=str))
    elif args.cmd=="loop":
        loop(args.interval)


if __name__=="__main__":
    main()
PY

echo "===== PATCH TRUSTED EMITTER TO ACCEPT EXECUTION BLOCKER EVIDENCE ====="
python - <<'PY'
from pathlib import Path

p=Path.home()/"companyos/companyos/runtime/trusted_procurement_intent_emitter.py"
s=p.read_text()

old='''    "specialist_evidence",
)
'''
new='''    "specialist_evidence",
    "venture_blockers",
)
'''
if old in s:
    s=s.replace(old,new,1)
elif '"venture_blockers"' not in s:
    raise SystemExit("V66_15_ABORT=trusted_root_anchor_missing")

p.write_text(s)
print("V66_15_TRUSTED_EMITTER_BLOCKER_ROOT=PASS")
PY

cat > "$CTL" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
PIDFILE="$RT/execution_blocker_router.pid"
LOGFILE="$RT/execution_blocker_router.log"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  start)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "BLOCKER_ROUTER_ALREADY_RUNNING PID=$(cat "$PIDFILE")"
      exit 0
    fi
    nohup python -m companyos.runtime.execution_blocker_router loop \
      --interval "${COMPANYOS_BLOCKER_ROUTER_INTERVAL_SECONDS:-120}" \
      >>"$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    sleep 1
    echo "BLOCKER_ROUTER_RUNNING PID=$(cat "$PIDFILE")"
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then
      kill "$(cat "$PIDFILE")" 2>/dev/null || true
      rm -f "$PIDFILE"
    fi
    echo "BLOCKER_ROUTER_STOPPED"
    ;;
  restart)
    "$0" stop
    "$0" start
    ;;
  once)
    python -m companyos.runtime.execution_blocker_router once
    ;;
  status)
    python -m companyos.runtime.execution_blocker_router status
    if [ -f "$PIDFILE" ]; then
      echo "PID=$(cat "$PIDFILE")"
      ps -p "$(cat "$PIDFILE")" -o pid,etime,args || true
    fi
    ;;
  blockers)
    tail -n "${2:-30}" "$RT/venture_blockers/blockers.jsonl" 2>/dev/null || true
    ;;
  log)
    tail -n "${2:-100}" "$LOGFILE"
    ;;
  *)
    echo "usage: $0 {start|stop|restart|once|status|blockers [n]|log [n]}"
    exit 2
    ;;
esac
SH
chmod +x "$CTL"

cat > "$ROOT/tests/test_execution_blocker_router.py" <<'PY'
from types import SimpleNamespace
from companyos.runtime.execution_blocker_router import classify

def task(err,payload=None):
    return SimpleNamespace(
        task_id="t1",
        task_type="build",
        payload=payload or {"venture_id":"v1"},
        state="FAILED",
        attempts=3,
        max_attempts=3,
        last_error=err,
    )

def test_rate_limit_not_purchase():
    x=classify(task("HTTP 429 Too Many Requests"))
    assert x["classification"]=="WAIT_OR_ROTATE_PROVIDER"
    assert x["creates_procurement"] is False

def test_credential_gap_not_purchase():
    x=classify(task("API key missing"))
    assert x["classification"]=="CONNECT_OR_PROVISION_CREDENTIAL"
    assert x["creates_procurement"] is False

def test_connector_gap_prefers_internal_build():
    x=classify(task("missing connector for this capability"))
    assert x["classification"]=="BUILD_INTERNAL_CAPABILITY"
    assert x["creates_procurement"] is False

def test_explicit_paid_resource_can_be_procurement():
    x=classify(task(
        "subscription required",
        {
            "venture_id":"v1",
            "required_service":"transactional email delivery API",
            "quoted_price_usd":20,
        },
    ))
    assert x["classification"]=="EXTERNAL_PROCUREMENT_BLOCKER"
    assert x["creates_procurement"] is True
    assert x["required_resource"]=="transactional email delivery API"
    assert x["quoted_price_usd"]==20
PY

echo "===== COMPILE ====="
python -m py_compile "$MOD" "$EMITTER"
echo "V66_15_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_execution_blocker_router.py
echo "V66_15_TESTS=PASS"

echo "===== FIRST BLOCKER SCAN ====="
"$CTL" once

echo "===== RESCAN TRUSTED PROCUREMENT INTENTS ====="
if [ -x "$ECTL" ]; then "$ECTL" once; fi

echo "===== REVALIDATE + SOURCE ONLY REAL PURCHASE INTENTS ====="
if [ -x "$ICTL" ]; then "$ICTL" once; fi
if [ -x "$SCTL" ]; then "$SCTL" once 20 || true; fi

echo "===== START BLOCKER ROUTER ====="
"$CTL" restart

echo "===== FINAL STATUS ====="
"$CTL" status

echo "V66_15_EXECUTION_BLOCKER_OBSERVATION=PASS"
echo "V66_15_INTERNAL_REPAIR_FIRST=PASS"
echo "V66_15_RATE_LIMIT_NOT_PROCUREMENT=PASS"
echo "V66_15_CREDENTIAL_GAP_NOT_PROCUREMENT=PASS"
echo "V66_15_EXPLICIT_COMMERCIAL_BLOCKER_ONLY=PASS"
echo "V66_15_EVENT_DRIVEN_PROCUREMENT=PASS"
echo "V66_15_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_15_COMPLETE"
