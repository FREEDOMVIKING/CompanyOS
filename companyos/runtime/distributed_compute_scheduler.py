from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from companyos.runtime import github_actions_worker_pool as pool
from companyos.runtime import adaptive_offload_controller as offload

ROOT=Path.home()/"companyos"
RT=Path.home()/".companyos_runtime"
STATE=RT/"distributed_compute_scheduler_state.json"
HISTORY=RT/"distributed_compute_scheduler_history.json"
VALIDATION_QUEUE=RT/"validation_experiment_queue.json"
EVIDENCE_QUEUE=RT/"evidence_acquisition_queue.json"

MAX_SHARDS=max(1,min(8,int(os.getenv("COMPANYOS_DISTRIBUTED_MAX_SHARDS","8"))))
MAX_INFLIGHT=max(1,min(4,int(os.getenv("COMPANYOS_DISTRIBUTED_MAX_INFLIGHT","3"))))
DAILY_CAP=max(1,int(os.getenv("COMPANYOS_DISTRIBUTED_DAILY_DISPATCH_CAP","30")))
MIN_GAP=max(30,int(os.getenv("COMPANYOS_DISTRIBUTED_MIN_DISPATCH_GAP_SECONDS","45")))
INTERVAL=max(30,int(os.getenv("COMPANYOS_DISTRIBUTED_SCHEDULER_SECONDS","60")))
RETRY_LIMIT=max(0,min(3,int(os.getenv("COMPANYOS_DISTRIBUTED_RETRY_LIMIT","2"))))
RETRY_DELAY=max(60,int(os.getenv("COMPANYOS_DISTRIBUTED_RETRY_DELAY_SECONDS","180")))
AUTO_PYTEST=os.getenv("COMPANYOS_DISTRIBUTED_AUTO_PYTEST","1")=="1"

def load(path:Path,default:Any):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def atomic(path:Path,obj:Any):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    tmp.replace(path)
    try:path.chmod(0o600)
    except Exception:pass

def git_sha()->str:
    try:
        return subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True,timeout=15).strip()
    except Exception:
        return "unknown"

def utc_day()->str:
    return time.strftime("%Y-%m-%d",time.gmtime())

def history()->dict[str,Any]:
    d=load(HISTORY,{"schema":"companyos.distributed_scheduler_history.v69_35c","days":{}})
    if not isinstance(d,dict):d={"schema":"companyos.distributed_scheduler_history.v69_35c","days":{}}
    if not isinstance(d.get("days"),dict):d["days"]={}
    return d

def dispatched_today()->int:
    row=history()["days"].get(utc_day()) or {}
    return int(row.get("dispatches") or 0)

def record_dispatch(job:dict[str,Any],reason:str)->None:
    d=history()
    day=d["days"].setdefault(utc_day(),{"dispatches":0,"jobs":[]})
    day["dispatches"]=int(day.get("dispatches") or 0)+1
    jobs=day.get("jobs") if isinstance(day.get("jobs"),list) else []
    jobs.append({"job_id":job.get("job_id"),"kind":job.get("kind"),"shards":job.get("shards"),"reason":reason,"created_at_unix":time.time()})
    day["jobs"]=jobs[-100:]
    d["days"]={k:v for k,v in d["days"].items() if k>=utc_day()}
    d["updated_at_unix"]=time.time()
    atomic(HISTORY,d)

def active_jobs()->list[dict[str,Any]]:
    return [j for j in pool.queue_state().get("jobs") or [] if isinstance(j,dict) and j.get("status") in {"queued","submitted","running"}]

def last_dispatch_unix()->float:
    times=[float(j.get("created_at_unix") or 0) for j in pool.queue_state().get("jobs") or [] if isinstance(j,dict)]
    return max(times) if times else 0.0

def can_enqueue()->tuple[bool,str]:
    if len(active_jobs())>=MAX_INFLIGHT:return False,"inflight_cap"
    if dispatched_today()>=DAILY_CAP:return False,"daily_cap"
    if time.time()-last_dispatch_unix()<MIN_GAP:return False,"dispatch_gap"
    auth=pool.gh_ready()
    if not auth.get("ready"):return False,str(auth.get("reason") or "gh_not_ready")
    return True,"ready"

def validation_backlog()->list[dict[str,Any]]:
    d=load(VALIDATION_QUEUE,{"experiments":[]})
    rows=[]
    for item in d.get("experiments") or []:
        if not isinstance(item,dict):continue
        if item.get("portfolio_active") is not True:continue
        if item.get("status") not in {"planned","inconclusive"}:continue
        query=str(item.get("query") or "").strip()
        if not query:continue
        rows.append({"query":query,"candidate_name":item.get("candidate_name"),"candidate_id":item.get("candidate_id"),"requirement":item.get("requirement"),"experiment_id":item.get("experiment_id")})
    return rows

def evidence_backlog_count()->int:
    d=load(EVIDENCE_QUEUE,{"tasks":[]})
    return sum(1 for x in d.get("tasks") or [] if isinstance(x,dict) and x.get("status") in {"research_required","queued","inconclusive"})

def shard_count(work_items:int,kind:str="research")->int:
    n=max(1,int(work_items))
    try:
        return offload.recommend_shards(
            kind=kind,
            work_items=n,
            queue=pool.queue_state(),
            max_shards=MAX_SHARDS,
        )
    except Exception:
        if n<=1:return 1
        if n<=3:return min(2,MAX_SHARDS,n)
        if n<=7:return min(4,MAX_SHARDS,n)
        return min(8,MAX_SHARDS,n)

def priority_score(validation_count:int,evidence_count:int)->int:
    return validation_count*3+evidence_count

def validation_dedupe(rows:list[dict[str,Any]])->str:
    ids=[str(x.get("experiment_id") or x.get("query") or "") for x in rows]
    return "scheduler_validation:"+hashlib.sha256("|".join(sorted(ids)).encode()).hexdigest()[:24]

def queue_validation(rows:list[dict[str,Any]])->dict[str,Any]|None:
    if not rows:return None
    batch=rows[:32]
    job=pool.enqueue("research",{"queries":batch,"max_results":8,"source":"distributed_compute_scheduler_v69_35c"},shards=shard_count(len(batch),"research"),dedupe_key=validation_dedupe(batch))
    record_dispatch(job,"validation_backlog")
    return job

def count_test_files()->int:
    return sum(1 for p in (ROOT/"tests").glob("test_*.py") if p.is_file())

def queue_pytest_if_needed(state:dict[str,Any])->dict[str,Any]|None:
    if not AUTO_PYTEST:return None
    sha=git_sha()
    if sha=="unknown" or state.get("last_pytest_sha")==sha:return None
    tests=count_test_files()
    if tests<=0:
        state["last_pytest_sha"]=sha
        return None
    job=pool.enqueue("pytest",{"timeout_seconds":15000},shards=shard_count(tests,"pytest"),dedupe_key="scheduler_pytest:"+sha)
    state["last_pytest_sha"]=sha
    record_dispatch(job,"new_source_sha")
    return job

def retry_failed_jobs()->dict[str,Any]|None:
    q=pool.queue_state()
    now=time.time()
    for old in reversed(q.get("jobs") or []):
        if not isinstance(old,dict) or old.get("status")!="failed":continue
        retries=int(old.get("scheduler_retry_count") or 0)
        if retries>=RETRY_LIMIT:continue
        updated=float(old.get("updated_at_unix") or old.get("created_at_unix") or 0)
        if now-updated<RETRY_DELAY:continue
        kind=str(old.get("kind") or "")
        if kind not in pool.ALLOWED:continue
        original=str(old.get("job_id") or "unknown")
        retry=pool.enqueue(kind,old.get("payload") if isinstance(old.get("payload"),dict) else {},shards=max(1,min(MAX_SHARDS,int(old.get("shards") or 1))),dedupe_key=f"retry:{original}:{retries+1}")
        retry["scheduler_retry_of"]=original
        retry["scheduler_retry_count"]=retries+1
        old["scheduler_retry_count"]=retries+1
        pool.atomic(pool.QUEUE,q)
        record_dispatch(retry,"failed_job_retry")
        return retry
    return None

def effectiveness()->dict[str,Any]:
    jobs=[j for j in pool.queue_state().get("jobs") or [] if isinstance(j,dict)]
    completed=[j for j in jobs if j.get("status")=="completed"]
    failed=[j for j in jobs if j.get("status") in {"failed","blocked"}]
    artifacts=attached=shards=0
    for j in completed:
        s=j.get("import_summary")
        if isinstance(s,dict):
            artifacts+=int(s.get("imported_artifacts") or 0)
            attached+=int(s.get("attached_evidence") or 0)
        shards+=int(j.get("shard_results") or 0)
    return {"jobs_total":len(jobs),"jobs_completed":len(completed),"jobs_failed_or_blocked":len(failed),"shard_results_collected":shards,"research_artifacts_imported":artifacts,"evidence_attachments":attached}

def once()->dict[str,Any]:
    state=load(STATE,{})
    validation=validation_backlog()
    evidence=evidence_backlog_count()
    auth=pool.gh_ready()
    allowed,reason=can_enqueue()
    job=None
    decision="none"

    if allowed:
        job=retry_failed_jobs()
        if job:
            decision="retry_failed_job"
        else:
            job=queue_pytest_if_needed(state)
            if job:
                decision="pytest_new_sha"
            elif validation:
                job=queue_validation(validation)
                decision="validation_research"

    telemetry=offload.snapshot(
        queue=pool.queue_state(),
        validation_backlog=len(validation),
        evidence_backlog=evidence,
        active_jobs=len(active_jobs()),
        max_shards=MAX_SHARDS,
    )

    out={
        "schema":"companyos.distributed_compute_scheduler_state.v69_35d",
        "updated_at_unix":time.time(),
        "healthy":True,
        "gh_ready":bool(auth.get("ready")),
        "decision":decision,
        "enqueue_allowed":allowed,
        "enqueue_block_reason":None if allowed else reason,
        "validation_backlog":len(validation),
        "evidence_backlog":evidence,
        "priority_score":priority_score(len(validation),evidence),
        "recommended_shards":shard_count(max(len(validation),1),"research"),
        "adaptive_offload":telemetry,
        "active_jobs":len(active_jobs()),
        "max_inflight":MAX_INFLIGHT,
        "daily_dispatches":dispatched_today(),
        "daily_dispatch_cap":DAILY_CAP,
        "max_shards":MAX_SHARDS,
        "queued_job_id":job.get("job_id") if isinstance(job,dict) else None,
        "queued_job_kind":job.get("kind") if isinstance(job,dict) else None,
        "queued_job_shards":job.get("shards") if isinstance(job,dict) else None,
        "effectiveness":effectiveness(),
        "external_messages_allowed":False,
        "financial_actions_allowed":False,
        "deployments_allowed":False,
        "account_creation_allowed":False,
    }
    if state.get("last_pytest_sha"):out["last_pytest_sha"]=state["last_pytest_sha"]
    atomic(STATE,out)
    return out

def loop()->None:
    while True:
        try:once()
        except Exception as exc:
            atomic(STATE,{"schema":"companyos.distributed_compute_scheduler_state.v69_35d","healthy":False,"updated_at_unix":time.time(),"error":f"{type(exc).__name__}:{str(exc)[:1000]}"})
        time.sleep(INTERVAL)

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("once","loop","status"))
    a=p.parse_args()
    if a.command=="once":
        print(json.dumps(once(),indent=2,sort_keys=True,default=str))
    elif a.command=="status":
        print(json.dumps({"scheduler":load(STATE,{"status":"not_run"}),"history":history(),"worker_pool":load(pool.STATE,{"status":"not_run"})},indent=2,sort_keys=True,default=str))
    else:
        loop()
    return 0

if __name__=="__main__":
    raise SystemExit(main())
