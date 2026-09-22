from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

RT=Path.home()/".companyos_runtime"
STATE=RT/"hybrid_compute_mesh_state.json"
HISTORY=RT/"hybrid_compute_mesh_history.jsonl"

SUPERVISOR=RT/"service_supervisor_state.json"
GITHUB_POOL=RT/"github_actions_worker_pool_state.json"
GITHUB_QUEUE=RT/"github_actions_worker_queue.json"
OFFLOAD=RT/"adaptive_offload_controller_state.json"
PROVISIONER=RT/"official_provider_provisioner_state.json"
REMOTE_INVENTORY=RT/"remote_runtime_hosts.json"
REMOTE_FABRIC=RT/"remote_runtime_fabric_state.json"
HOST_SCOUT=RT/"persistent_host_scout_state.json"

INTERVAL=max(30,int(os.getenv("COMPANYOS_HYBRID_COMPUTE_MESH_SECONDS","60")))
MAX_HISTORY=max(50,min(2000,int(os.getenv("COMPANYOS_HYBRID_COMPUTE_MESH_HISTORY_LIMIT","500"))))


def load(path:Path,default:Any):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def atomic(path:Path,obj:Any)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    tmp.replace(path)
    try:path.chmod(0o600)
    except Exception:pass


def append_history(obj:dict[str,Any])->None:
    HISTORY.parent.mkdir(parents=True,exist_ok=True)
    with HISTORY.open("a",encoding="utf-8") as f:
        f.write(json.dumps(obj,sort_keys=True,default=str)+"\n")
    try:
        rows=HISTORY.read_text(encoding="utf-8").splitlines()
        if len(rows)>MAX_HISTORY:
            HISTORY.write_text("\n".join(rows[-MAX_HISTORY:])+"\n",encoding="utf-8")
    except Exception:
        pass


def local_plane()->dict[str,Any]:
    sup=load(SUPERVISOR,{})
    services=sup.get("services") if isinstance(sup,dict) else {}
    if not isinstance(services,dict):services={}
    running=sum(1 for row in services.values() if isinstance(row,dict) and row.get("running") is True)
    return {
        "plane":"termux_local",
        "healthy":bool(sup.get("running") and running>0),
        "supervisor_running":bool(sup.get("running")),
        "services_running":running,
        "services_total":len(services),
        "configured_capacity_lanes":1,
    }


def github_plane()->dict[str,Any]:
    state=load(GITHUB_POOL,{})
    queue=load(GITHUB_QUEUE,{"jobs":[]})
    jobs=queue.get("jobs") if isinstance(queue,dict) else []
    if not isinstance(jobs,list):jobs=[]

    inflight=sum(1 for j in jobs if isinstance(j,dict) and j.get("status") in {"queued","submitted","running"})
    completed=sum(1 for j in jobs if isinstance(j,dict) and j.get("status")=="completed")
    failed=sum(1 for j in jobs if isinstance(j,dict) and j.get("status") in {"failed","blocked"})
    terminal=completed+failed
    success=(completed/terminal) if terminal else 1.0

    max_inflight=max(1,int(state.get("max_inflight") or os.getenv("COMPANYOS_GITHUB_ACTIONS_MAX_INFLIGHT","2")))
    max_shards=max(1,min(8,int(os.getenv("COMPANYOS_DISTRIBUTED_MAX_SHARDS","8"))))
    gh_ready=bool(state.get("gh_ready"))
    return {
        "plane":"github_actions_burst",
        "healthy":bool(state.get("healthy",True) and gh_ready),
        "gh_ready":gh_ready,
        "queued_or_inflight_jobs":inflight,
        "completed_jobs":completed,
        "failed_or_blocked_jobs":failed,
        "observed_success_rate":round(success,4),
        "configured_max_inflight_workflows":max_inflight,
        "configured_max_shards_per_workflow":max_shards,
        "configured_burst_lane_ceiling":max_inflight*max_shards,
        "guaranteed_concurrency":False,
        "ephemeral":True,
    }


def remote_plane()->dict[str,Any]:
    inv=load(REMOTE_INVENTORY,{"nodes":[]})
    fabric=load(REMOTE_FABRIC,{"nodes":[]})
    nodes=inv.get("nodes") if isinstance(inv,dict) else []
    probes=fabric.get("nodes") if isinstance(fabric,dict) else []
    if not isinstance(nodes,list):nodes=[]
    if not isinstance(probes,list):probes=[]

    health_by_name={
        str(x.get("name")):bool(x.get("healthy"))
        for x in probes if isinstance(x,dict) and x.get("name")
    }

    enrolled=[]
    healthy=[]
    healthy_primary=[]
    capacity=0.0
    for node in nodes:
        if not isinstance(node,dict) or not node.get("enabled",True):continue
        name=str(node.get("name") or "")
        role=str(node.get("role") or "")
        row={
            "name":name,
            "provider":node.get("provider"),
            "role":role,
            "healthy":health_by_name.get(name,False),
            "capacity_score":float(node.get("capacity_score") or 1.0),
        }
        enrolled.append(row)
        if row["healthy"]:
            healthy.append(row)
            capacity+=row["capacity_score"]
            if role=="primary":healthy_primary.append(row)

    return {
        "plane":"persistent_remote_fabric",
        "healthy":bool(healthy),
        "enrolled_node_count":len(enrolled),
        "healthy_node_count":len(healthy),
        "healthy_primary_count":len(healthy_primary),
        "healthy_capacity_score":round(capacity,2),
        "nodes":enrolled,
        "persistent":True,
    }


def provider_plane()->dict[str,Any]:
    state=load(PROVISIONER,{})
    readiness=state.get("readiness") if isinstance(state,dict) else {}
    if not isinstance(readiness,dict):readiness={}
    action=state.get("action") if isinstance(state.get("action"),dict) else {}
    return {
        "plane":"official_provider_activation",
        "healthy":bool(state.get("healthy",True)),
        "credential_ready_count":int(readiness.get("credential_ready_count") or 0),
        "best_ready_provider":readiness.get("best_ready_provider"),
        "auto_provision_enabled":bool(state.get("auto_provision_enabled")),
        "last_action_performed":bool(action.get("performed")),
        "last_action_reason":action.get("reason"),
        "max_monthly_usd":state.get("max_monthly_usd"),
        "financial_action_performed_by_mesh":False,
    }


def host_discovery_plane()->dict[str,Any]:
    scout=load(HOST_SCOUT,{})
    top=scout.get("top_candidate") if isinstance(scout,dict) else None
    if isinstance(top,dict):
        top={
            "host_id":top.get("host_id"),
            "provider":top.get("provider"),
            "kind":top.get("kind"),
            "score":top.get("score"),
            "monthly_cost_usd":top.get("monthly_cost_usd"),
            "credential_present":top.get("credential_present"),
            "always_on_expected":top.get("always_on_expected"),
        }
    return {
        "plane":"persistent_host_discovery",
        "healthy":bool(scout.get("healthy",True)) if isinstance(scout,dict) else True,
        "active_host_search":bool(scout.get("active_host_search")) if isinstance(scout,dict) else False,
        "dynamic_discoveries_count":int(scout.get("dynamic_discoveries_count") or 0) if isinstance(scout,dict) else 0,
        "top_candidate":top,
    }


def offload_plane()->dict[str,Any]:
    state=load(OFFLOAD,{})
    ext=state.get("external") if isinstance(state.get("external"),dict) else {}
    phone=state.get("phone") if isinstance(state.get("phone"),dict) else {}
    return {
        "plane":"adaptive_offload",
        "healthy":bool(state.get("healthy",True)),
        "mode":state.get("mode"),
        "recommended_shards":state.get("recommended_shards"),
        "phone_pressure_score":phone.get("phone_pressure_score"),
        "external_success_rate":ext.get("external_success_rate"),
        "average_external_turnaround_seconds":ext.get("average_turnaround_seconds"),
    }


def choose_operating_mode(local,github,remote,provider)->dict[str,Any]:
    if remote.get("healthy_primary_count",0)>0:
        return {
            "mode":"remote_primary_plus_burst" if github.get("healthy") else "remote_primary",
            "primary_control_plane":"persistent_remote",
            "fallback_control_plane":"termux_local",
            "burst_compute_plane":"github_actions" if github.get("healthy") else None,
            "persistent_remote_available":True,
            "next_action":"keep_remote_primary_healthy",
        }

    if provider.get("credential_ready_count",0)>0:
        next_action="provider_provisioner_ready" if provider.get("auto_provision_enabled") else "provider_ready_but_auto_provision_disabled"
    else:
        next_action="continue_host_discovery_and_wait_for_official_provider_credentials"

    return {
        "mode":"phone_control_plus_github_burst" if github.get("healthy") else "phone_only",
        "primary_control_plane":"termux_local",
        "fallback_control_plane":"none",
        "burst_compute_plane":"github_actions" if github.get("healthy") else None,
        "persistent_remote_available":bool(remote.get("healthy")),
        "next_action":next_action,
    }


def once()->dict[str,Any]:
    started=time.time()
    local=local_plane()
    github=github_plane()
    remote=remote_plane()
    provider=provider_plane()
    scout=host_discovery_plane()
    offload=offload_plane()
    operating=choose_operating_mode(local,github,remote,provider)

    out={
        "schema":"companyos.hybrid_compute_mesh.v69_38",
        "updated_at_unix":time.time(),
        "scan_seconds":round(time.time()-started,4),
        "healthy":bool(local.get("healthy") or remote.get("healthy")),
        "operating":operating,
        "capacity":{
            "local_control_lanes":1 if local.get("healthy") else 0,
            "configured_github_burst_lane_ceiling":int(github.get("configured_burst_lane_ceiling") or 0),
            "persistent_remote_capacity_score":float(remote.get("healthy_capacity_score") or 0),
            "github_concurrency_is_guaranteed":False,
        },
        "planes":{
            "local":local,
            "github":github,
            "persistent_remote":remote,
            "official_provider":provider,
            "host_discovery":scout,
            "adaptive_offload":offload,
        },
        "restrictions":{
            "mesh_financial_actions":False,
            "mesh_account_creation":False,
            "mesh_provider_signup":False,
            "mesh_deployment_actions":False,
            "quota_bypass":False,
            "credential_harvesting":False,
        },
        "secret_values_emitted":False,
    }
    atomic(STATE,out)
    append_history({
        "ts":out["updated_at_unix"],
        "healthy":out["healthy"],
        "mode":operating["mode"],
        "primary":operating["primary_control_plane"],
        "github_burst_healthy":github.get("healthy"),
        "persistent_remote_healthy":remote.get("healthy"),
        "healthy_remote_nodes":remote.get("healthy_node_count"),
        "provider_credential_ready_count":provider.get("credential_ready_count"),
        "recommended_shards":offload.get("recommended_shards"),
    })
    return out


def status()->dict[str,Any]:
    return load(STATE,{"status":"not_run","state_path":str(STATE)})


def loop()->None:
    while True:
        try:once()
        except Exception as exc:
            atomic(STATE,{
                "schema":"companyos.hybrid_compute_mesh.v69_38",
                "updated_at_unix":time.time(),
                "healthy":False,
                "error":f"{type(exc).__name__}:{str(exc)[:1200]}",
                "secret_values_emitted":False,
            })
        time.sleep(INTERVAL)


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("once","status","loop"))
    a=p.parse_args()
    if a.command=="once":out=once()
    elif a.command=="status":out=status()
    else:
        loop()
        return 0
    print(json.dumps(out,indent=2,sort_keys=True,default=str))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
