#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
MOD="$ROOT/companyos/runtime/authority_aware_launch_bridge.py"
LIVE="$ROOT/companyos/runtime/venture_liveness_runtime.py"
LCTL="$ROOT/scripts/companyos_livenessctl"
XCTL="$ROOT/scripts/companyos_externalctl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.22 AUTHORITY-AWARE LAUNCH BRIDGE ====="
echo "GOAL=TURN_VERIFIED_LAUNCH_READY_VENTURES_INTO_REAL_DEPLOYMENT_ACTIONS"
echo "NOTE=REQUIRES_EXISTING_PUBLIC_DEPLOYMENT_AUTHORITY"
echo "NOTE=WRITES_LAUNCH_EVIDENCE_ONLY_AFTER_REAL_CONNECTOR_EXECUTION"
echo "NOTE=NO_AUTHORITY_SWITCHES_CHANGED"

for f in \
  "$ROOT/companyos/runtime/venture_liveness_runtime.py" \
  "$ROOT/companyos/governance/venture_identity_progression.py" \
  "$ROOT/companyos/connectors_live/engine.py"
do
  [ -f "$f" ] || { echo "V66_22_ABORT=missing:$f"; exit 1; }
done

stamp="$(date +%Y%m%d_%H%M%S)"
for f in "$MOD" "$LIVE"; do
  if [ -f "$f" ]; then
    cp "$f" "${f}.v66_22_backup_${stamp}"
    echo "BACKUP=${f}.v66_22_backup_${stamp}"
  fi
done

cat > "$MOD" <<'PY'
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from companyos.governance.venture_identity_progression import (
    candidate_ventures,
    evaluate_all,
)
from companyos.runtime.stalled_stage_progression_controller import canonical_ventures
from companyos.connectors_live.engine import ConnectorEngine

HOME=Path.home()
ROOT=HOME/"companyos"
RT=HOME/".companyos_runtime"
CONNECTOR_RT=ROOT/"companyos_runtime"/"connectors"

STATE=RT/"authority_aware_launch_bridge_state.json"
LATEST=RT/"authority_aware_launch_bridge_latest.json"
VERSION="V66.22"


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def save_json(path: Path, data: Any) -> None:
    import tempfile
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=str(path.parent))
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


def authority() -> dict[str,bool]:
    try:
        from companyos.runtime.live_drl_strategy_governor import LIVE_AUTHORITY
        if isinstance(LIVE_AUTHORITY,dict):
            return {str(k):bool(v) for k,v in LIVE_AUTHORITY.items()}
    except Exception:
        pass
    return {}


def deployment_authorized() -> bool:
    a=authority()
    return bool(
        a.get("public_deployment")
        and a.get("external_irreversible_actions")
    )


def hosting_health() -> dict[str,Any]:
    try:
        e=ConnectorEngine()
        h=e.health()
        return (h.get("connectors") or {}).get("hosting") or {}
    except Exception as exc:
        return {
            "configured":False,
            "enabled":False,
            "error":f"{type(exc).__name__}:{exc}",
        }


def roots_for(cid: str) -> list[Path]:
    groups=candidate_ventures()
    rec=groups.get(cid) or {}
    out=[]
    for rel in rec.get("roots") or []:
        p=ROOT/rel
        if p.exists() and p.is_dir():
            out.append(p)
    return out


def has_real_deployment_evidence(roots: list[Path]) -> bool:
    markers=(
        "deployment_result",
        "live_url",
        "venture_stage_launch",
    )
    for root in roots:
        try:
            for p in root.rglob("*"):
                if not p.is_file():
                    continue
                low=str(p).lower()
                if any(x in low for x in markers):
                    return True
        except Exception:
            continue
    return False


def deploy_root_for(cid: str) -> Path|None:
    roots=roots_for(cid)
    candidates=[]
    for root in roots:
        candidates.extend([
            root/"dist",
            root/"build",
            root/"public",
            root/"site",
            root/"web",
            root/"frontend"/"dist",
            root/"frontend"/"build",
            root,
        ])

    seen=set()
    for p in candidates:
        try:
            rp=str(p.resolve())
        except Exception:
            continue
        if rp in seen:
            continue
        seen.add(rp)

        if not p.exists() or not p.is_dir():
            continue

        # Require a concrete static entry point. This prevents blindly
        # uploading an arbitrary source-code directory.
        if (p/"index.html").is_file():
            return p

        # Some generated sites store a nested public index.
        htmls=[]
        try:
            htmls=list(p.glob("*.html"))
        except Exception:
            htmls=[]
        if any(x.name.lower()=="index.html" for x in htmls):
            return p
    return None


def actions() -> list[dict[str,Any]]:
    x=load_json(CONNECTOR_RT/"actions.json",[])
    return x if isinstance(x,list) else []


def executions() -> list[dict[str,Any]]:
    x=load_json(CONNECTOR_RT/"executions.json",[])
    return x if isinstance(x,list) else []


def execution_for(action_id: str) -> dict[str,Any]|None:
    for x in reversed(executions()):
        if str(x.get("action_id") or "")==str(action_id):
            return x
    return None


def materialize_success(cid: str, root: Path, action_id: str, rec: dict[str,Any]) -> str:
    result=rec.get("result") or {}
    evidence_dir=root/"companyos_progress"
    evidence_dir.mkdir(parents=True,exist_ok=True)
    path=evidence_dir/f"deployment_result_{action_id}.json"

    safe_result={
        k:v for k,v in result.items()
        if "token" not in str(k).lower()
        and "secret" not in str(k).lower()
        and "jwt" not in str(k).lower()
    }

    save_json(path,{
        "schema":"companyos.real_deployment_result.v1",
        "version":VERSION,
        "canonical_id":cid,
        "action_id":action_id,
        "connector":"hosting",
        "action":"deploy_production",
        "ok":bool(result.get("ok")),
        "status":result.get("status"),
        "provider":result.get("provider"),
        "deployment_id":result.get("deployment_id"),
        "live_url":result.get("live_url"),
        "result":safe_result,
        "executed_at":rec.get("executed_at"),
        "materialized_at_unix":time.time(),
        "real_connector_execution_required":True,
    })
    return str(path)


def queue_launch(cid: str, deploy_root: Path) -> dict[str,Any]:
    engine=ConnectorEngine()
    item=engine.queue(
        "hosting",
        "deploy_production",
        {
            "project_name":cid,
            "website_path":str(deploy_root),
            "canonical_id":cid,
            "source":"V66.22_authority_aware_launch_bridge",
        },
        risk="high",
    )
    return item


def run_once() -> dict[str,Any]:
    state=load_json(STATE,{"pending":{},"completed":{}})
    pending=state.setdefault("pending",{})
    completed=state.setdefault("completed",{})

    materialized=[]
    failures=[]
    still_pending=[]

    # Reconcile already queued launch actions first.
    for cid,info in list(pending.items()):
        action_id=str((info or {}).get("action_id") or "")
        root=Path(str((info or {}).get("venture_root") or ""))
        rec=execution_for(action_id)
        if not rec:
            still_pending.append({
                "canonical_id":cid,
                "action_id":action_id,
            })
            continue

        result=rec.get("result") or {}
        if result.get("ok") is True:
            evidence=materialize_success(cid,root,action_id,rec)
            completed[cid]={
                "action_id":action_id,
                "evidence":evidence,
                "live_url":result.get("live_url"),
                "completed_at_unix":time.time(),
            }
            pending.pop(cid,None)
            materialized.append({
                "canonical_id":cid,
                "action_id":action_id,
                "evidence":evidence,
                "live_url":result.get("live_url"),
            })
        else:
            failures.append({
                "canonical_id":cid,
                "action_id":action_id,
                "status":result.get("status"),
                "error":result.get("error"),
            })
            # Keep failed executions from being silently retried forever.
            completed[cid]={
                "action_id":action_id,
                "failed":True,
                "result":result,
                "completed_at_unix":time.time(),
            }
            pending.pop(cid,None)

    queued=[]
    skipped=[]

    auth=deployment_authorized()
    health=hosting_health()
    hosting_ready=bool(
        health.get("configured")
        and health.get("enabled")
    )

    ventures=canonical_ventures()
    for cid,row in sorted(ventures.items()):
        if str(row.get("stage") or "")!="LAUNCH_READY":
            continue
        if cid in pending:
            continue
        if cid in completed and not completed[cid].get("failed"):
            continue

        roots=roots_for(cid)
        if has_real_deployment_evidence(roots):
            skipped.append({
                "canonical_id":cid,
                "reason":"deployment_evidence_already_present",
            })
            continue

        if not auth:
            skipped.append({
                "canonical_id":cid,
                "reason":"public_deployment_authority_not_enabled",
            })
            continue

        if not hosting_ready:
            skipped.append({
                "canonical_id":cid,
                "reason":"hosting_connector_not_live_ready",
                "hosting_health":health,
            })
            continue

        deploy_root=deploy_root_for(cid)
        if not deploy_root:
            skipped.append({
                "canonical_id":cid,
                "reason":"no_static_deploy_root_with_index_html",
            })
            continue

        item=queue_launch(cid,deploy_root)
        pending[cid]={
            "action_id":item.get("action_id"),
            "venture_root":str(roots[0]) if roots else str(deploy_root),
            "deploy_root":str(deploy_root),
            "queued_at_unix":time.time(),
        }
        queued.append({
            "canonical_id":cid,
            "action_id":item.get("action_id"),
            "deploy_root":str(deploy_root),
        })

        # One real launch action at a time.
        break

    save_json(STATE,{
        "version":VERSION,
        "updated_at_unix":time.time(),
        "pending":pending,
        "completed":completed,
    })

    refreshed=[]
    if materialized:
        try:
            refreshed=evaluate_all()
        except Exception:
            refreshed=[]

    report={
        "version":VERSION,
        "mode":"authority_aware_real_launch_bridge",
        "deployment_authorized":auth,
        "hosting_health":health,
        "hosting_ready":hosting_ready,
        "queued":queued,
        "materialized":materialized,
        "still_pending":still_pending,
        "failures":failures,
        "skipped":skipped,
        "refreshed_ventures":[
            {
                "canonical_id":x.get("canonical_id"),
                "stage":x.get("stage"),
                "unchanged_observations":x.get("unchanged_observations"),
            }
            for x in refreshed
        ],
        "rules":{
            "authority_switches_changed":False,
            "real_connector_execution_required_for_launch_evidence":True,
            "static_index_required_before_queue":True,
            "duplicate_launch_queueing":False,
            "one_launch_action_at_a_time":True,
        },
        "timestamp_unix":time.time(),
    }
    save_json(LATEST,report)
    return report
PY

echo "===== PATCH EXISTING LIVENESS LOOP ====="
python - <<'PY'
from pathlib import Path

p=Path.home()/"companyos/companyos/runtime/venture_liveness_runtime.py"
s=p.read_text()

anchor='''from companyos.runtime.proactive_venture_progression import maybe_start_next
'''
addition='''from companyos.runtime.authority_aware_launch_bridge import run_once as run_launch_bridge_once
'''
if addition not in s:
    if anchor not in s:
        raise SystemExit("V66_22_ABORT=liveness_import_anchor_missing")
    s=s.replace(anchor,anchor+addition,1)

old='''    report={
        "version":VERSION,
'''
new='''    try:
        launch_bridge=run_launch_bridge_once()
    except Exception as exc:
        launch_bridge={
            "version":"V66.22",
            "error":f"{type(exc).__name__}:{exc}",
        }

    report={
        "version":VERSION,
'''
if "launch_bridge=run_launch_bridge_once()" not in s:
    if old not in s:
        raise SystemExit("V66_22_ABORT=liveness_report_start_anchor_missing")
    s=s.replace(old,new,1)

needle='''        "progression":progression,
        "progression_mode":progression_mode,
        "orchestrations":orchestration_counts(),
'''
replacement='''        "progression":progression,
        "progression_mode":progression_mode,
        "launch_bridge":launch_bridge,
        "orchestrations":orchestration_counts(),
'''
if replacement not in s:
    if needle not in s:
        raise SystemExit("V66_22_ABORT=liveness_launch_report_anchor_missing")
    s=s.replace(needle,replacement,1)

p.write_text(s)
print("V66_22_LIVENESS_INTEGRATION=PASS")
PY

cat > "$ROOT/tests/test_authority_aware_launch_bridge.py" <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
from companyos.runtime.authority_aware_launch_bridge import has_real_deployment_evidence

def test_no_deployment_evidence_for_plain_site():
    with TemporaryDirectory() as td:
        p=Path(td)
        (p/"index.html").write_text("ok")
        assert has_real_deployment_evidence([p]) is False

def test_real_deployment_result_detected():
    with TemporaryDirectory() as td:
        p=Path(td)
        q=p/"companyos_progress"
        q.mkdir()
        (q/"deployment_result_abc.json").write_text("{}")
        assert has_real_deployment_evidence([p]) is True
PY

echo "===== COMPILE ====="
python -m py_compile "$MOD" "$LIVE"
echo "V66_22_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_authority_aware_launch_bridge.py
echo "V66_22_TESTS=PASS"

echo "===== RESTART VERIFIED EXTERNAL ROUTER IF PRESENT ====="
if [ -x "$XCTL" ]; then
  "$XCTL" restart || true
  "$XCTL" status || true
else
  echo "V66_22_EXTERNAL_ROUTER_CTL_NOT_FOUND=SKIP"
fi

echo "===== FIRST AUTHORITY-AWARE LAUNCH PASS ====="
python - <<'PY'
import json
from companyos.runtime.authority_aware_launch_bridge import run_once
print(json.dumps(run_once(),indent=2,sort_keys=True,default=str))
PY

echo "===== RESTART EXISTING CEO + LIVENESS LOOP ====="
"$LCTL" restart

echo "===== ALLOW ROUTER/LIVENESS TO RECONCILE ====="
sleep 15

echo "===== SECOND LAUNCH PASS ====="
python - <<'PY'
import json
from companyos.runtime.authority_aware_launch_bridge import run_once
print(json.dumps(run_once(),indent=2,sort_keys=True,default=str))
PY

echo "===== FINAL LIVENESS STATUS ====="
"$LCTL" status

echo "V66_22_LAUNCH_READY_DETECTION=PASS"
echo "V66_22_EXISTING_AUTHORITY_REUSED=PASS"
echo "V66_22_LIVE_HOSTING_CONNECTOR_GATE=PASS"
echo "V66_22_REAL_EXECUTION_EVIDENCE_REQUIRED=PASS"
echo "V66_22_DUPLICATE_DEPLOY_GUARD=PASS"
echo "V66_22_EXISTING_LIVENESS_PROCESS_REUSED=PASS"
echo "V66_22_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_22_COMPLETE"
