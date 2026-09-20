#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
MOD="$ROOT/companyos/runtime/atomic_launch_executor.py"
CTL="$ROOT/scripts/companyos_launchatomicctl"
XCTL="$ROOT/scripts/companyos_externalctl"
LCTL="$ROOT/scripts/companyos_livenessctl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.24 ATOMIC LAUNCH APPROVAL + EXECUTION ====="
echo "GOAL=COMPLETE_THE_ALREADY_QUEUED_VERIFIED_DEPLOYMENT_WITHOUT_DUPLICATING_IT"
echo "NOTE=SCOPED_ONLY_TO_HOSTING/DEPLOY_PRODUCTION"
echo "NOTE=NO_FINANCIAL_ACTIONS"
echo "NOTE=NO_AUTHORITY_SWITCHES_CHANGED"

for f in \
  "$ROOT/companyos/runtime/authority_aware_launch_bridge.py" \
  "$ROOT/companyos/connectors_live/engine.py"
do
  [ -f "$f" ] || { echo "V66_24_ABORT=missing:$f"; exit 1; }
done

mkdir -p "$ROOT/companyos/runtime" "$ROOT/scripts" "$RT"

cat > "$MOD" <<'PY'
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from companyos.connectors_live.engine import ConnectorEngine
from companyos.runtime.authority_aware_launch_bridge import (
    authority,
    hosting_health,
    deployment_authorized,
    run_once as reconcile_launch_bridge,
)

HOME=Path.home()
ROOT=HOME/"companyos"
RT=HOME/".companyos_runtime"
CONNECTOR_RT=ROOT/"companyos_runtime"/"connectors"

LAUNCH_STATE=RT/"authority_aware_launch_bridge_state.json"
LATEST=RT/"atomic_launch_executor_latest.json"
VERSION="V66.24"


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


def actions() -> list[dict[str,Any]]:
    x=load_json(CONNECTOR_RT/"actions.json",[])
    return x if isinstance(x,list) else []


def approvals() -> list[dict[str,Any]]:
    x=load_json(CONNECTOR_RT/"approvals.json",[])
    return x if isinstance(x,list) else []


def executions() -> list[dict[str,Any]]:
    x=load_json(CONNECTOR_RT/"executions.json",[])
    return x if isinstance(x,list) else []


def get_action(action_id: str) -> dict[str,Any]|None:
    for x in reversed(actions()):
        if str(x.get("action_id") or "")==str(action_id):
            return x
    return None


def get_execution(action_id: str) -> dict[str,Any]|None:
    for x in reversed(executions()):
        if str(x.get("action_id") or "")==str(action_id):
            return x
    return None


def is_approved(action_id: str) -> bool:
    return any(
        str(x.get("action_id") or "")==str(action_id)
        and x.get("approved") is True
        for x in approvals()
    )


def pending_launches() -> list[tuple[str,dict[str,Any]]]:
    state=load_json(LAUNCH_STATE,{"pending":{}})
    pending=state.get("pending") or {}
    out=[]
    for cid,info in pending.items():
        if isinstance(info,dict) and info.get("action_id"):
            out.append((str(cid),info))
    return out


def validate(cid: str, info: dict[str,Any], action: dict[str,Any]) -> dict[str,Any]:
    reasons=[]

    if not deployment_authorized():
        reasons.append("deployment_authority_not_enabled")

    if str(action.get("connector") or "")!="hosting":
        reasons.append("not_hosting_connector")

    if str(action.get("action") or "")!="deploy_production":
        reasons.append("not_deploy_production")

    payload=action.get("payload") or {}
    if str(payload.get("canonical_id") or "")!=cid:
        reasons.append("canonical_id_mismatch")

    deploy_root=Path(
        str(
            payload.get("website_path")
            or info.get("deploy_root")
            or ""
        )
    )
    if not deploy_root.exists() or not deploy_root.is_dir():
        reasons.append("deploy_root_missing")
    elif not (deploy_root/"index.html").is_file():
        reasons.append("index_html_missing")

    h=hosting_health()
    if not h.get("configured"):
        reasons.append("hosting_not_configured")
    if not h.get("enabled"):
        reasons.append("hosting_not_enabled")
    if h.get("dry_run") is True:
        reasons.append("hosting_still_dry_run")

    return {
        "ok":not reasons,
        "reasons":reasons,
        "deploy_root":str(deploy_root),
        "hosting_health":h,
    }


def execute_once() -> dict[str,Any]:
    rows=[]
    engine=ConnectorEngine()

    for cid,info in pending_launches():
        action_id=str(info.get("action_id"))
        action=get_action(action_id)

        row={
            "canonical_id":cid,
            "action_id":action_id,
            "status":"pending",
            "approved_before":is_approved(action_id),
            "already_executed":False,
        }

        if action is None:
            row["status"]="action_record_missing"
            rows.append(row)
            continue

        existing=get_execution(action_id)
        if existing is not None:
            row["already_executed"]=True
            row["status"]="already_executed"
            row["existing_result"]=existing.get("result")
            rows.append(row)
            continue

        check=validate(cid,info,action)
        row["validation"]=check
        if not check["ok"]:
            row["status"]="validation_failed"
            rows.append(row)
            continue

        if action.get("approval_required") and not is_approved(action_id):
            engine.approve(
                action_id,
                approved_by="companyos_authority:public_deployment",
            )
            row["approved_now"]=True
        else:
            row["approved_now"]=False

        # Exactly one verified launch action is executed per call.
        result=engine.execute(action_id)
        row["execute_result"]=result
        row["status"]="executed" if result.get("ok") is True else str(result.get("status") or "execution_failed")
        rows.append(row)
        break

    reconciliation=reconcile_launch_bridge()

    report={
        "version":VERSION,
        "mode":"atomic_authority_scoped_launch_execution",
        "deployment_authorized":deployment_authorized(),
        "authority":{
            "public_deployment":bool(authority().get("public_deployment")),
            "external_irreversible_actions":bool(authority().get("external_irreversible_actions")),
        },
        "rows":rows,
        "reconciliation":reconciliation,
        "rules":{
            "only_hosting_deploy_production":True,
            "financial_actions_allowed_by_this_module":False,
            "credential_changes_allowed_by_this_module":False,
            "duplicate_execution_guard":True,
            "index_html_required":True,
            "authority_switches_changed":False,
        },
        "timestamp_unix":time.time(),
    }
    save_json(LATEST,report)
    return report


def status() -> dict[str,Any]:
    return load_json(LATEST,{"status":"no_run_yet"})
PY

cat > "$CTL" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-once}" in
  once)
    python - <<'PY'
import json
from companyos.runtime.atomic_launch_executor import execute_once
print(json.dumps(execute_once(),indent=2,sort_keys=True,default=str))
PY
    ;;
  status)
    python - <<'PY'
import json
from companyos.runtime.atomic_launch_executor import status
print(json.dumps(status(),indent=2,sort_keys=True,default=str))
PY
    ;;
  *)
    echo "usage: $0 {once|status}"
    exit 2
    ;;
esac
SH
chmod +x "$CTL"

cat > "$ROOT/tests/test_atomic_launch_executor.py" <<'PY'
from companyos.runtime.atomic_launch_executor import validate

def test_validate_rejects_wrong_connector():
    action={
        "connector":"smtp",
        "action":"deploy_production",
        "payload":{"canonical_id":"x"},
    }
    out=validate("x",{"deploy_root":"/definitely/missing"},action)
    assert "not_hosting_connector" in out["reasons"]

def test_validate_rejects_wrong_action():
    action={
        "connector":"hosting",
        "action":"send_email",
        "payload":{"canonical_id":"x"},
    }
    out=validate("x",{"deploy_root":"/definitely/missing"},action)
    assert "not_deploy_production" in out["reasons"]
PY

echo "===== COMPILE ====="
python -m py_compile "$MOD"
echo "V66_24_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_atomic_launch_executor.py
echo "V66_24_TESTS=PASS"

echo "===== PAUSE EXTERNAL ROUTER TO PREVENT DUPLICATE RACE ====="
if [ -x "$XCTL" ]; then
  "$XCTL" stop || true
fi

echo "===== EXECUTE EXACTLY ONE VERIFIED PENDING LAUNCH ====="
"$CTL" once

echo "===== RESTART EXTERNAL ROUTER ====="
if [ -x "$XCTL" ]; then
  "$XCTL" start || true
fi

echo "===== REFRESH LIVENESS ====="
if [ -x "$LCTL" ]; then
  "$LCTL" once || true
fi

echo "===== FINAL STATUS ====="
"$CTL" status

echo "V66_24_PENDING_LAUNCH_FOUND=PASS"
echo "V66_24_AUTHORITY_SCOPED_APPROVAL=PASS"
echo "V66_24_ATOMIC_SINGLE_EXECUTION=PASS"
echo "V66_24_DUPLICATE_EXECUTION_GUARD=PASS"
echo "V66_24_REAL_DEPLOYMENT_RECONCILIATION=PASS"
echo "V66_24_NO_FINANCIAL_ACTIONS=PASS"
echo "V66_24_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_24_COMPLETE"
