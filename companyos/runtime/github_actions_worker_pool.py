from __future__ import annotations
import argparse, base64, hashlib, json, os, shutil, subprocess, time
from pathlib import Path
from typing import Any

ROOT=Path.home()/"companyos"
RT=Path.home()/".companyos_runtime"
QUEUE=RT/"github_actions_worker_queue.json"
STATE=RT/"github_actions_worker_pool_state.json"
RESULTS=RT/"github_actions_results"
VALIDATION_QUEUE=RT/"validation_experiment_queue.json"
EVIDENCE_QUEUE=RT/"evidence_acquisition_queue.json"
CANONICAL=RT/"canonical_research_outputs"

REPO=os.getenv("COMPANYOS_GITHUB_REPO","FREEDOMVIKING/CompanyOS")
WORKFLOW=os.getenv("COMPANYOS_GITHUB_WORKFLOW","companyos-worker-pool.yml")
WORKFLOW_REF=os.getenv("COMPANYOS_GITHUB_WORKFLOW_REF","main")
SOURCE_REF=os.getenv("COMPANYOS_GITHUB_SOURCE_REF","companyos-continuous-fix-2026-09-11")
DEFAULT_SHARDS=max(1,min(8,int(os.getenv("COMPANYOS_GITHUB_ACTIONS_SHARDS","4"))))
MAX_INFLIGHT=max(1,min(4,int(os.getenv("COMPANYOS_GITHUB_ACTIONS_MAX_INFLIGHT","2"))))
POLL=max(30,int(os.getenv("COMPANYOS_GITHUB_ACTIONS_POLL_SECONDS","60")))
ALLOWED={"smoke","research","pytest"}

def load(path:Path,default:Any):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception:return default

def atomic(path:Path,obj:Any):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    tmp.replace(path)
    try:path.chmod(0o600)
    except Exception:pass

def run(cmd:list[str],timeout:int=60):
    return subprocess.run(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=False,timeout=timeout)

def gh_ready():
    gh=shutil.which("gh")
    if not gh:return {"ready":False,"reason":"gh_not_installed"}
    p=run([gh,"auth","status","-h","github.com"],20)
    return {"ready":p.returncode==0,"reason":"ok" if p.returncode==0 else "gh_not_authenticated"}

def queue_state():
    d=load(QUEUE,{"schema":"companyos.github_actions_worker_queue.v69_35b","jobs":[]})
    if not isinstance(d,dict):d={"jobs":[]}
    if not isinstance(d.get("jobs"),list):d["jobs"]=[]
    return d

def encode(payload):
    return base64.urlsafe_b64encode(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).decode()

def enqueue(kind,payload,shards=DEFAULT_SHARDS,dedupe_key=None):
    if kind not in ALLOWED:raise ValueError("unsupported_task_kind")
    q=queue_state()
    if dedupe_key:
        for j in q["jobs"]:
            if isinstance(j,dict) and j.get("dedupe_key")==dedupe_key and j.get("status") in {"queued","submitted","running","completed"}:
                return j
    job_id="ga_"+hashlib.sha256((json.dumps(payload,sort_keys=True,default=str)+str(time.time_ns())).encode()).hexdigest()[:20]
    job={"job_id":job_id,"kind":kind,"payload":payload,"shards":max(1,min(8,int(shards))),
         "source_ref":SOURCE_REF,"status":"queued","dedupe_key":dedupe_key,
         "dispatch_attempts":0,"created_at_unix":time.time(),"updated_at_unix":time.time()}
    q["jobs"].append(job); q["jobs"]=q["jobs"][-300:]; atomic(QUEUE,q)
    return job

def gh_json(args,timeout=60):
    gh=shutil.which("gh")
    if not gh:raise RuntimeError("gh_not_installed")
    p=run([gh,*args],timeout)
    if p.returncode:raise RuntimeError(p.stderr[-1000:] or "gh_failed")
    return json.loads(p.stdout or "null")

def dispatch(job):
    if not gh_ready()["ready"]:raise RuntimeError("gh_not_ready")
    shards=max(1,min(8,int(job.get("shards") or 1)))
    payload=encode(job.get("payload") or {})
    if len(payload)>50000:raise RuntimeError("payload_too_large")
    gh=shutil.which("gh")
    p=run([gh,"workflow","run",WORKFLOW,"--repo",REPO,"--ref",WORKFLOW_REF,
           "-f","job_id="+job["job_id"],"-f","source_ref="+str(job.get("source_ref") or SOURCE_REF),
           "-f","task_kind="+job["kind"],"-f","payload_b64="+payload,
           "-f","shards_json="+json.dumps(list(range(shards)),separators=(",",":")),
           "-f","shard_count="+str(shards)],60)
    if p.returncode:raise RuntimeError(p.stderr[-1200:] or "workflow_dispatch_failed")
    job["dispatch_attempts"]=int(job.get("dispatch_attempts") or 0)+1
    job["status"]="submitted"
    job["dispatched_at_unix"]=time.time()
    job["updated_at_unix"]=job["dispatched_at_unix"]
    deadline=time.time()+45
    while time.time()<deadline:
        rows=gh_json(["run","list","--repo",REPO,"--workflow",WORKFLOW,"--event","workflow_dispatch",
                      "--limit","50","--json","databaseId,displayTitle,status,conclusion"],30) or []
        for r in rows:
            if r.get("displayTitle")=="CompanyOS Worker "+job["job_id"]:
                job["run_id"]=int(r["databaseId"]); job["status"]="running" if r.get("status")!="completed" else "completed"
                return job
        time.sleep(3)
    return job

def attach(candidate,requirement,artifact):
    q=load(EVIDENCE_QUEUE,{"tasks":[]}); tasks=q.get("tasks") if isinstance(q,dict) else []
    if not isinstance(tasks,list):tasks=[]
    task=next((x for x in tasks if isinstance(x,dict) and x.get("candidate_name")==candidate and x.get("requirement")==requirement),None)
    if task is None:
        task={"task_id":hashlib.sha256((candidate+"|"+requirement).encode()).hexdigest()[:20],
              "candidate_name":candidate,"requirement":requirement,"status":"research_required",
              "external_send_allowed":False,"financial_action_allowed":False,"deployment_allowed":False}
        tasks.append(task)
    arts=task.get("evidence_artifacts") if isinstance(task.get("evidence_artifacts"),list) else []
    if str(artifact) not in {str(x.get("path") if isinstance(x,dict) else x) for x in arts}:
        arts.append({"path":str(artifact),"source":"github_actions_worker_pool_v69_35b","observed_at":time.time()})
    task["evidence_artifacts"]=arts[-30:]; task["status"]="observed"; task["observed_at"]=time.time()
    q={"tasks":tasks[-500:]}; atomic(EVIDENCE_QUEUE,q)

def import_results(job,shards):
    if job.get("kind")!="research":return {"imported_artifacts":0,"attached_evidence":0}
    CANONICAL.mkdir(parents=True,exist_ok=True); imported=attached_count=0
    for shard in shards:
        for out in shard.get("outcomes") or []:
            if not isinstance(out,dict):continue
            meta=out.get("metadata") if isinstance(out.get("metadata"),dict) else {}
            candidate=str(meta.get("candidate_name") or ""); requirement=str(meta.get("requirement") or "")
            urls={str(x.get("url") or "") for x in out.get("results") or [] if isinstance(x,dict) and x.get("url")}
            digest=hashlib.sha256((job["job_id"]+str(out.get("query"))).encode()).hexdigest()[:18]
            artifact=CANONICAL/f"github_actions_research_{digest}_{int(time.time()*1000)}.json"
            artifact.write_text(json.dumps({
                "schema":"companyos.github_actions_research.v69_35b","job_id":job["job_id"],
                "run_id":job.get("run_id"),"query":out.get("query"),"candidate_name":candidate or None,
                "requirement":requirement or None,"provider":out.get("provider"),
                "source_rows":out.get("results") or [],"distinct_url_count":len(urls),
                "economic_values_modified":False
            },indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
            imported+=1
            if candidate and requirement and out.get("status")=="success" and len(urls)>=2:
                attach(candidate,requirement,artifact); attached_count+=1
    return {"imported_artifacts":imported,"attached_evidence":attached_count}

def collect(job):
    if not job.get("run_id"):return job
    data=gh_json(["run","view",str(job["run_id"]),"--repo",REPO,
                  "--json","status,conclusion,databaseId,displayTitle,url"],30)
    if data.get("status")!="completed":
        job["status"]="running"; return job
    if data.get("conclusion")!="success":
        job["status"]="failed"
        job["github_conclusion"]=data.get("conclusion")
        job["completed_at_unix"]=time.time()
        job["updated_at_unix"]=job["completed_at_unix"]
        return job
    target=RESULTS/job["job_id"]
    if target.exists():shutil.rmtree(target)
    target.mkdir(parents=True,exist_ok=True)
    gh=shutil.which("gh")
    p=run([gh,"run","download",str(job["run_id"]),"--repo",REPO,"--dir",str(target)],180)
    if p.returncode:raise RuntimeError(p.stderr[-1000:] or "download_failed")
    shards=[]
    for f in target.rglob("result.json"):
        try:
            x=json.loads(f.read_text(encoding="utf-8"))
            if isinstance(x,dict):shards.append(x)
        except Exception:pass
    job["import_summary"]=import_results(job,shards)
    job["status"]="completed"
    job["shard_results"]=len(shards)
    job["completed_at_unix"]=time.time()
    job["updated_at_unix"]=job["completed_at_unix"]
    return job

def seed_validation():
    d=load(VALIDATION_QUEUE,{"experiments":[]}); queries=[]; ids=[]
    for row in d.get("experiments") or []:
        if not isinstance(row,dict) or row.get("portfolio_active") is not True or row.get("status") not in {"planned","inconclusive"}:continue
        q=str(row.get("query") or "").strip()
        if not q:continue
        queries.append({"query":q,"candidate_name":row.get("candidate_name"),"requirement":row.get("requirement"),
                        "experiment_id":row.get("experiment_id")})
        ids.append(str(row.get("experiment_id") or q))
        if len(queries)>=24:break
    if not queries:return None
    key="validation:"+hashlib.sha256("|".join(sorted(ids)).encode()).hexdigest()[:24]
    return enqueue("research",{"queries":queries,"max_results":8},min(DEFAULT_SHARDS,len(queries)),key)

def cycle():
    auth=gh_ready()
    # COMPANYOS_V69_35C_SCHEDULER_OWNS_SEEDING
    scheduler_owns_seeding=(
        os.getenv("COMPANYOS_ENABLE_DISTRIBUTED_SCHEDULER","1")=="1"
        and (ROOT/"companyos/runtime/distributed_compute_scheduler.py").exists()
    )
    if not scheduler_owns_seeding:
        try:seed_validation()
        except Exception:pass
    q=queue_state(); jobs=q["jobs"]
    inflight=sum(1 for j in jobs if isinstance(j,dict) and j.get("status") in {"submitted","running"})
    if auth["ready"]:
        for j in jobs:
            if inflight>=MAX_INFLIGHT:break
            if not isinstance(j,dict) or j.get("status")!="queued":continue
            try:dispatch(j); inflight+=1
            except Exception as exc:
                j["dispatch_attempts"]=int(j.get("dispatch_attempts") or 0)+1
                j["last_error"]=f"{type(exc).__name__}:{str(exc)[:800]}"
                if j["dispatch_attempts"]>=3:j["status"]="blocked"
        for j in jobs:
            if isinstance(j,dict) and j.get("status") in {"submitted","running"}:
                try:collect(j)
                except Exception as exc:j["last_collect_error"]=f"{type(exc).__name__}:{str(exc)[:800]}"
    q["jobs"]=jobs[-300:]; atomic(QUEUE,q)
    state={"schema":"companyos.github_actions_worker_pool_state.v69_35d","healthy":True,
           "updated_at_unix":time.time(),"gh_ready":auth["ready"],"gh_reason":auth["reason"],
           "default_shards":DEFAULT_SHARDS,"max_inflight":MAX_INFLIGHT,
           "queued":sum(1 for j in jobs if isinstance(j,dict) and j.get("status")=="queued"),
           "inflight":sum(1 for j in jobs if isinstance(j,dict) and j.get("status") in {"submitted","running"}),
           "completed":sum(1 for j in jobs if isinstance(j,dict) and j.get("status")=="completed")}
    atomic(STATE,state); return state

def loop():
    while True:
        try:cycle()
        except Exception as exc:atomic(STATE,{"healthy":False,"error":f"{type(exc).__name__}:{str(exc)[:800]}","updated_at_unix":time.time()})
        time.sleep(POLL)

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd",required=True)
    for name in ("status","cycle","loop","seed-validation"):sub.add_parser(name)
    e=sub.add_parser("enqueue"); e.add_argument("--kind",required=True,choices=sorted(ALLOWED)); e.add_argument("--payload-json",required=True); e.add_argument("--shards",type=int,default=DEFAULT_SHARDS)
    a=p.parse_args()
    if a.cmd=="status":print(json.dumps({"state":load(STATE,{}),"queue":queue_state(),"auth":gh_ready()},indent=2,sort_keys=True))
    elif a.cmd=="cycle":print(json.dumps(cycle(),indent=2,sort_keys=True))
    elif a.cmd=="loop":loop()
    elif a.cmd=="seed-validation":print(json.dumps(seed_validation(),indent=2,sort_keys=True,default=str))
    else:print(json.dumps(enqueue(a.kind,json.loads(a.payload_json),a.shards),indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
