from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from companyos.governance.venture_identity_progression import (
    candidate_ventures,
    artifact_files,
    infer_stage,
    verified_external_stage,
)
from companyos.runtime.stalled_stage_progression_controller import canonical_ventures

HOME=Path.home()
ROOT=HOME/"companyos"
RT=HOME/".companyos_runtime"
LRT=ROOT/".companyos_runtime"

IDENTITY=LRT/"venture_identity_progression.json"
LIVENESS=RT/"venture_liveness_latest.json"
OUTCOME=RT/"canonical_outcome_bridge_latest.json"
CEO=RT/"autonomous_ceo_runtime_service.json"
LATEST=RT/"canonical_state_reconciliation_latest.json"
HISTORY=RT/"canonical_state_reconciliation_history.jsonl"

VERSION="V66.19"


def load_json(path: Path,default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def save_json(path: Path,data: Any) -> None:
    import os,tempfile
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


def append_jsonl(path: Path,row: dict[str,Any]) -> None:
    with path.open("a") as f:
        f.write(json.dumps(row,sort_keys=True,default=str)+"\n")


def stage_markers(files: list[Path]) -> list[str]:
    names=" ".join(str(p).lower() for p in files)
    markers=[]
    checks=(
        ("venture_stage_scale","SCALE"),
        ("venture_stage_operate","OPERATE"),
        ("venture_stage_customer_acquisition","CUSTOMER_ACQUISITION"),
        ("venture_stage_launch","LAUNCH"),
        ("venture_stage_launch_ready","LAUNCH_READY"),
        ("venture_stage_package","PACKAGE"),
        ("venture_stage_test","TEST"),
        ("venture_stage_build","BUILD"),
        ("venture_stage_validate","VALIDATE"),
        ("conversion_result","CUSTOMER_ACQUISITION"),
        ("customer_result","CUSTOMER_ACQUISITION"),
        ("lead_result","CUSTOMER_ACQUISITION"),
        ("outreach_result","CUSTOMER_ACQUISITION"),
        ("campaign_result","CUSTOMER_ACQUISITION"),
        ("deployment_result","LAUNCH"),
        ("live_url","LAUNCH"),
        ("export_manifest","LAUNCH_READY"),
        ("test_result","TEST"),
        ("qa_result","TEST"),
        ("acceptance_result","TEST"),
        ("validation_result","VALIDATE"),
    )
    for marker,stage in checks:
        if marker in names:
            markers.append(f"{marker}:{stage}")
    if any(p.suffix.lower()==".zip" for p in files):
        markers.append("zip_artifact:LAUNCH_READY")
    return markers


def current_candidates() -> dict[str,Any]:
    groups=candidate_ventures()
    identity=load_json(IDENTITY,{"ventures":{}})
    idrows=identity.get("ventures") or {}

    out={}
    for cid,rec in groups.items():
        fs=artifact_files(rec)
        state=idrows.get(cid,{})
        out[cid]={
            "canonical_id":cid,
            "aliases":rec.get("aliases") or [],
            "roots":rec.get("roots") or [],
            "artifact_count_live":len(fs),
            "inferred_stage_live":infer_stage(fs),
            "verified_external_stage_live":verified_external_stage(fs),
            "stage_markers":stage_markers(fs),
            "state_stage":state.get("stage"),
            "state_artifact_count":state.get("artifact_count"),
            "unchanged_observations":state.get("unchanged_observations"),
            "changed_since_previous_observation":state.get("changed_since_previous_observation"),
        }
    return out


def run_once() -> dict[str,Any]:
    cand=current_candidates()
    canonical=canonical_ventures()
    live=load_json(LIVENESS,{})
    outcome=load_json(OUTCOME,{})
    ceo=load_json(CEO,{})

    stale_latest=((live.get("canonical") or {}).get("canonical_ventures") != len(canonical))

    report={
        "version":VERSION,
        "mode":"canonical_state_reconciliation_audit",
        "candidate_ventures":len(cand),
        "canonical_ventures":len(canonical),
        "liveness_latest_canonical_count":(live.get("canonical") or {}).get("canonical_ventures"),
        "liveness_latest_is_stale":bool(stale_latest),
        "current_stalled_3plus":sum(
            1 for x in canonical.values()
            if int(x.get("unchanged_observations") or 0)>=3
        ),
        "current_stalled_5plus":sum(
            1 for x in canonical.values()
            if int(x.get("unchanged_observations") or 0)>=5
        ),
        "ventures":cand,
        "outcome_bridge_materialized_total":len(
            (load_json(RT/"canonical_outcome_bridge_state.json",{"processed":[]}).get("processed") or [])
        ),
        "ceo_runtime":{
            "running":ceo.get("running"),
            "ready":ceo.get("ready"),
            "active_orchestrations":ceo.get("active_orchestrations"),
            "completed_orchestrations":ceo.get("completed_orchestrations"),
            "cycle_count":ceo.get("cycle_count"),
            "last_cycle_unix":ceo.get("last_cycle_unix"),
        },
        "rules":{
            "venture_content_mutated":False,
            "stage_advanced":False,
            "duplicate_venture_created":False,
            "authority_switches_changed":False,
        },
        "timestamp_unix":time.time(),
    }

    save_json(LATEST,report)
    append_jsonl(HISTORY,report)
    return report


def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("once")
    sub.add_parser("status")
    args=ap.parse_args()

    if args.cmd=="once":
        print(json.dumps(run_once(),indent=2,sort_keys=True,default=str))
    else:
        print(json.dumps(load_json(LATEST,{}),indent=2,sort_keys=True,default=str))


if __name__=="__main__":
    main()
