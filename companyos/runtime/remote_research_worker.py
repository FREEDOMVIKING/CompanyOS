from __future__ import annotations
import argparse, base64, json, os, time

os.environ["COMPANYOS_REMOTE_WORKER_LOCAL_ONLY"]="1"
from companyos.runtime import provider_connector_router as pcr

def decode(v:str)->str:
    return base64.urlsafe_b64decode(v.encode("ascii")).decode("utf-8")

def search(query:str,max_results:int=8)->dict:
    started=time.time()
    out=pcr.search_web(query,max_results=max_results)
    return {
        "schema":"companyos.remote_research_worker.v69_35a",
        "healthy":True,
        "provider":out.get("provider"),
        "results":out.get("results") or [],
        "result_count":int(out.get("result_count") or 0),
        "attempts":out.get("attempts") or [],
        "latency_seconds":round(time.time()-started,3),
        "read_only":True,
        "external_messages_sent":False,
        "financial_actions_performed":False,
        "deployments_performed":False,
        "account_creation_performed":False,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("search","health"))
    p.add_argument("--query-b64",default="")
    p.add_argument("--max-results",type=int,default=8)
    a=p.parse_args()
    if a.command=="health":
        print(json.dumps({"healthy":True,"role":"research_worker","read_only":True}))
        return 0
    print(json.dumps(search(decode(a.query_b64),max(1,min(12,a.max_results))),sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
