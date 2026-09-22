from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import time
from pathlib import Path
from typing import Any

RT=Path.home()/".companyos_runtime"
QUEUE=RT/"github_actions_worker_queue.json"
STATE=RT/"adaptive_offload_controller_state.json"
HISTORY=RT/"adaptive_offload_telemetry.jsonl"
HISTORY_LIMIT=max(24,min(2000,int(os.getenv("COMPANYOS_ADAPTIVE_OFFLOAD_HISTORY_LIMIT","240"))))


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


def clamp(v:float,lo:float=0.0,hi:float=1.0)->float:
    return max(lo,min(hi,float(v)))


def _meminfo()->dict[str,int]:
    out={}
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8",errors="replace").splitlines():
            if ":" not in line:continue
            key,val=line.split(":",1)
            token=val.strip().split()[0]
            out[key]=int(token)
    except Exception:
        pass
    return out


def phone_metrics()->dict[str,Any]:
    cpu_count=max(1,int(os.cpu_count() or 1))
    try:
        load1=float(os.getloadavg()[0])
    except Exception:
        try:
            load1=float(Path("/proc/loadavg").read_text().split()[0])
        except Exception:
            load1=0.0
    load_ratio=clamp(load1/cpu_count)

    mem=_meminfo()
    total=max(1,int(mem.get("MemTotal") or 1))
    available=max(0,int(mem.get("MemAvailable") or mem.get("MemFree") or 0))
    memory_used_ratio=clamp(1.0-(available/total))

    pressure=clamp((load_ratio*0.70)+(memory_used_ratio*0.30))
    return {
        "cpu_count":cpu_count,
        "load1":round(load1,3),
        "load_ratio":round(load_ratio,4),
        "memory_used_ratio":round(memory_used_ratio,4),
        "phone_pressure_score":round(pressure,4),
    }


def worker_metrics(queue:dict[str,Any],recent_limit:int=24)->dict[str,Any]:
    jobs=[j for j in queue.get("jobs") or [] if isinstance(j,dict)]
    jobs=sorted(jobs,key=lambda j:float(j.get("updated_at_unix") or j.get("created_at_unix") or 0))[-recent_limit:]
    terminal=[j for j in jobs if j.get("status") in {"completed","failed","blocked"}]
    completed=[j for j in terminal if j.get("status")=="completed"]
    failed=[j for j in terminal if j.get("status") in {"failed","blocked"}]
    success_rate=(len(completed)/len(terminal)) if terminal else 1.0

    durations=[]
    for j in terminal:
        start=float(j.get("dispatched_at_unix") or j.get("created_at_unix") or 0)
        end=float(j.get("completed_at_unix") or j.get("updated_at_unix") or 0)
        if start>0 and end>=start:
            durations.append(end-start)

    avg=statistics.fmean(durations) if durations else None
    p95=None
    if durations:
        ordered=sorted(durations)
        idx=max(0,min(len(ordered)-1,math.ceil(len(ordered)*0.95)-1))
        p95=ordered[idx]

    inflight=sum(1 for j in jobs if j.get("status") in {"queued","submitted","running"})
    return {
        "recent_jobs":len(jobs),
        "terminal_jobs":len(terminal),
        "successful_jobs":len(completed),
        "failed_or_blocked_jobs":len(failed),
        "external_success_rate":round(success_rate,4),
        "average_turnaround_seconds":None if avg is None else round(avg,2),
        "p95_turnaround_seconds":None if p95 is None else round(p95,2),
        "current_inflight_jobs":inflight,
    }


def baseline_shards(work_items:int,max_shards:int=8)->int:
    n=max(1,int(work_items))
    cap=max(1,min(8,int(max_shards)))
    if n<=1:return 1
    if n<=3:return min(2,cap,n)
    if n<=7:return min(4,cap,n)
    return min(8,cap,n)


def decide(
    *,
    kind:str,
    work_items:int,
    queue:dict[str,Any],
    max_shards:int=8,
    phone:dict[str,Any]|None=None,
)->dict[str,Any]:
    phone=phone or phone_metrics()
    workers=worker_metrics(queue)
    pressure=float(phone.get("phone_pressure_score") or 0)
    reliability=float(workers.get("external_success_rate") or 0)
    samples=int(workers.get("terminal_jobs") or 0)
    avg=workers.get("average_turnaround_seconds")

    shards=baseline_shards(work_items,max_shards)
    mode="balanced"

    if pressure>=0.80 and work_items>=4:
        shards=min(max_shards,8,max(shards,8))
        mode="remote_max"
    elif pressure>=0.60 and work_items>=2:
        shards=min(max_shards,max(shards,4))
        mode="remote_accelerated"
    elif pressure<=0.30 and work_items<=3:
        shards=min(shards,2)
        mode="local_light"

    if samples>=4 and reliability<0.50:
        shards=min(shards,1)
        mode="degraded_external"
    elif samples>=4 and reliability<0.75:
        shards=min(shards,2)
        mode="cautious_external"

    if isinstance(avg,(int,float)) and avg>1200:
        shards=min(shards,2)
        if mode not in {"degraded_external","cautious_external"}:
            mode="slow_external"

    if kind=="pytest" and work_items>=8 and reliability>=0.75:
        shards=max(shards,min(max_shards,4))

    shards=max(1,min(int(max_shards),8,int(shards),max(1,int(work_items))))
    remote_share=1.0 if kind=="pytest" else round(min(1.0,0.35+(pressure*0.65)),2)

    return {
        "mode":mode,
        "kind":kind,
        "work_items":int(work_items),
        "recommended_shards":shards,
        "remote_share_hint":remote_share,
        "phone":phone,
        "external":workers,
        "reason":{
            "phone_pressure":pressure,
            "external_success_rate":reliability,
            "terminal_samples":samples,
            "turnaround_seconds":avg,
        },
        "quota_bypass_allowed":False,
        "arbitrary_shell_payloads_allowed":False,
        "financial_actions_allowed":False,
        "account_creation_allowed":False,
        "deployments_allowed":False,
    }


def recommend_shards(
    *,
    kind:str,
    work_items:int,
    queue:dict[str,Any],
    max_shards:int=8,
)->int:
    return int(decide(kind=kind,work_items=work_items,queue=queue,max_shards=max_shards)["recommended_shards"])


def snapshot(
    *,
    queue:dict[str,Any]|None=None,
    validation_backlog:int=0,
    evidence_backlog:int=0,
    active_jobs:int=0,
    max_shards:int=8,
)->dict[str,Any]:
    q=queue if isinstance(queue,dict) else load(QUEUE,{"jobs":[]})
    work=max(1,int(validation_backlog)+int(evidence_backlog))
    rec=decide(kind="research",work_items=work,queue=q,max_shards=max_shards)
    out={
        "schema":"companyos.adaptive_offload_controller.v69_35d",
        "updated_at_unix":time.time(),
        "healthy":True,
        "validation_backlog":int(validation_backlog),
        "evidence_backlog":int(evidence_backlog),
        "active_jobs":int(active_jobs),
        **rec,
    }
    atomic(STATE,out)
    HISTORY.parent.mkdir(parents=True,exist_ok=True)
    with HISTORY.open("a",encoding="utf-8") as f:
        f.write(json.dumps(out,sort_keys=True,default=str)+"\n")
    _trim_history()
    return out


def _trim_history()->None:
    try:
        lines=HISTORY.read_text(encoding="utf-8").splitlines()
        if len(lines)>HISTORY_LIMIT:
            HISTORY.write_text("\n".join(lines[-HISTORY_LIMIT:])+"\n",encoding="utf-8")
    except Exception:
        pass


def status()->dict[str,Any]:
    return {
        "state":load(STATE,{"status":"not_run"}),
        "phone_now":phone_metrics(),
        "worker_now":worker_metrics(load(QUEUE,{"jobs":[]})),
        "history_path":str(HISTORY),
    }


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("status","sample","recommend"))
    p.add_argument("--kind",default="research",choices=("research","pytest","smoke"))
    p.add_argument("--work-items",type=int,default=1)
    p.add_argument("--max-shards",type=int,default=8)
    a=p.parse_args()
    q=load(QUEUE,{"jobs":[]})
    if a.command=="status":
        out=status()
    elif a.command=="sample":
        out=snapshot(queue=q,max_shards=a.max_shards)
    else:
        out=decide(kind=a.kind,work_items=a.work_items,queue=q,max_shards=a.max_shards)
    print(json.dumps(out,indent=2,sort_keys=True,default=str))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
