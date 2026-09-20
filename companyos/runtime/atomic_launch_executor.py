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
