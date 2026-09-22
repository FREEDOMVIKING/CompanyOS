from __future__ import annotations
import argparse, base64, json, os, platform, subprocess, sys, time
from pathlib import Path
from typing import Any

os.environ["COMPANYOS_REMOTE_WORKER_LOCAL_ONLY"]="1"
os.environ["COMPANYOS_GITHUB_ACTIONS_WORKER"]="1"
ALLOWED_KINDS={"smoke","research","pytest"}

def decode_payload(value:str)->dict[str,Any]:
    obj=json.loads(base64.urlsafe_b64decode(value.encode()).decode())
    if not isinstance(obj,dict): raise ValueError("payload_must_be_object")
    return obj

def shard_items(items:list[Any],shard:int,shard_count:int)->list[Any]:
    count=max(1,int(shard_count)); shard=int(shard)
    if shard<0 or shard>=count: raise ValueError("invalid_shard")
    return list(items)[shard::count]

def execute(job_id:str,kind:str,payload:dict[str,Any],shard:int,shard_count:int)->dict[str,Any]:
    kind=kind.strip().lower()
    if kind not in ALLOWED_KINDS: raise ValueError("unsupported_task_kind")
    common={
        "job_id":job_id,"kind":kind,"shard":shard,"shard_count":shard_count,
        "external_messages_sent":False,"financial_actions_performed":False,
        "deployments_performed":False,"account_creation_performed":False,
    }
    if kind=="smoke":
        return {**common,"healthy":True,"python":sys.version.split()[0],
                "platform":platform.platform(),"cpu_count":os.cpu_count()}

    if kind=="research":
        from companyos.runtime import provider_connector_router as pcr
        entries=payload.get("queries") or []
        if not isinstance(entries,list): raise ValueError("queries_must_be_list")
        outcomes=[]
        for item in shard_items(entries,shard,shard_count):
            meta={"query":item} if isinstance(item,str) else dict(item) if isinstance(item,dict) else {}
            query=str(meta.pop("query","")).strip()
            if not query: continue
            started=time.time()
            try:
                result=pcr.search_web(query,max_results=max(1,min(12,int(payload.get("max_results") or 8))))
                outcomes.append({
                    "query":query,"metadata":meta,"status":"success",
                    "provider":result.get("provider"),"results":result.get("results") or [],
                    "result_count":int(result.get("result_count") or 0),
                    "attempts":result.get("attempts") or [],
                    "latency_seconds":round(time.time()-started,3),
                })
            except Exception as exc:
                outcomes.append({
                    "query":query,"metadata":meta,"status":"failed","results":[],
                    "result_count":0,"error":f"{type(exc).__name__}:{str(exc)[:800]}",
                })
        return {**common,"healthy":True,"outcomes":outcomes,"query_count":len(outcomes)}

    requested=payload.get("test_paths") or []
    if requested and not isinstance(requested,list): raise ValueError("test_paths_must_be_list")
    if requested:
        files=[str(Path(x)) for x in requested if str(x).startswith("tests") and Path(x).is_file()]
    else:
        files=[str(x) for x in sorted(Path("tests").glob("test_*.py")) if x.is_file()]
    selected=shard_items(files,shard,shard_count)
    if not selected:
        return {**common,"healthy":True,"returncode":0,"selected_test_files":[],"stdout_tail":"NO_TESTS_ASSIGNED"}
    proc=subprocess.run(
        [sys.executable,"-m","pytest","-q",*selected],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=False,
        timeout=min(18000,max(60,int(payload.get("timeout_seconds") or 15000))),
    )
    return {
        **common,"healthy":proc.returncode==0,"returncode":proc.returncode,
        "selected_test_files":selected,"stdout_tail":proc.stdout[-12000:],
        "stderr_tail":proc.stderr[-8000:],
    }

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("execute",))
    p.add_argument("--job-id",required=True)
    p.add_argument("--kind",required=True,choices=sorted(ALLOWED_KINDS))
    p.add_argument("--payload-b64",required=True)
    p.add_argument("--shard",type=int,required=True)
    p.add_argument("--shard-count",type=int,required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    out=execute(a.job_id,a.kind,decode_payload(a.payload_b64),a.shard,a.shard_count)
    out["completed_at_unix"]=time.time()
    path=Path(a.output); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    print(json.dumps({"job_id":a.job_id,"shard":a.shard,"healthy":bool(out.get("healthy"))}))
    return 0 if out.get("healthy") else 1

if __name__=="__main__":
    raise SystemExit(main())
