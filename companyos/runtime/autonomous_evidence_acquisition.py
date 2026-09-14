from __future__ import annotations
import hashlib, json, os, re, time
from pathlib import Path

ROOT=Path.home()/"companyos"
RT=ROOT/".companyos_runtime"
STATE=RT/"evidence_acquisition_state.json"
QUEUE=RT/"evidence_acquisition_queue.json"
EVENTS=RT/"evidence_acquisition_events.jsonl"
STOP=RT/"STOP_CONTINUOUS"
ACTION_QUEUE=RT/"profit_execution_action_queue.json"
RESEARCH_DIR=RT/"canonical_research_outputs"

REQUIREMENTS={
    "provenance":"Identify source origin/ownership and preserve a retrievable reference.",
    "recency":"Confirm observation date/freshness and record the timestamp.",
    "authority":"Assess source authority or qualification for the specific claim.",
    "corroboration":"Find an independent second source for material claims.",
    "relevance":"Map evidence directly to the candidate claim or qualification criterion.",
    "traceability":"Record source reference, timestamp, claim, and review note.",
    "pricing":"Collect evidence for market price/willingness-to-pay from a credible source.",
    "buyer_demand":"Collect concrete buyer/customer demand evidence.",
    "competition":"Collect current competitor/substitute evidence.",
}

def load(path,default=None):
    if default is None: default={}
    try:return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:return default

def atomic(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    tmp.replace(path)

def emit(kind,**kw):
    EVENTS.parent.mkdir(parents=True,exist_ok=True)
    with EVENTS.open("a",encoding="utf-8") as f:
        f.write(json.dumps({"ts":time.time(),"kind":kind,**kw},sort_keys=True,default=str)+"\n")

def slug(v):
    s=re.sub(r"[^a-zA-Z0-9_]+","_",str(v or "")).strip("_").lower()
    return re.sub(r"_+","_",s)

def latest_action_packet():
    q=load(ACTION_QUEUE,{"actions":[]})
    rows=q.get("actions",[]) if isinstance(q,dict) else []
    rows=[r for r in rows if isinstance(r,dict)]
    return rows[-1] if rows else None

def requirements_from_packet(packet):
    reqs=[];seen=set()
    def add(kind,detail,source):
        key=slug(kind)
        if not key or key in seen:return
        seen.add(key)
        reqs.append({"requirement":key,"guidance":detail or REQUIREMENTS.get(key,"Collect concrete, attributable evidence for this requirement."),"source":source})

    for row in packet.get("capability_results",[]) or []:
        if not isinstance(row,dict) or not row.get("ok"):continue
        result=row.get("result")
        if not isinstance(result,dict):continue

        ev=result.get("evidence_requirements")
        if isinstance(ev,list):
            for item in ev:
                if isinstance(item,dict):
                    add(item.get("requirement") or item.get("id") or "evidence",item.get("guidance"),row.get("capability_id"))
                elif isinstance(item,str):
                    add(item,None,row.get("capability_id"))

        tb=result.get("top_bottleneck")
        if isinstance(tb,dict):
            reason=slug(tb.get("reason"))
            if reason=="missing_external_evidence":
                for key in ("provenance","recency","authority","corroboration","relevance","traceability"):
                    add(key,REQUIREMENTS[key],row.get("capability_id"))
            elif reason=="profit_unestimated":
                add("pricing",REQUIREMENTS["pricing"],row.get("capability_id"))
            elif reason=="probability_unestimated":
                add("buyer_demand",REQUIREMENTS["buyer_demand"],row.get("capability_id"))

    blob=json.dumps(packet,default=str).lower()
    if "price hypothesis" in blob or "pricing" in blob:
        add("pricing",REQUIREMENTS["pricing"],"action_packet")
    if "buyer" in blob or "customer" in blob:
        add("buyer_demand",REQUIREMENTS["buyer_demand"],"action_packet")
    return reqs

def build_tasks(packet,requirements):
    candidate=str(packet.get("candidate_name") or "unknown_candidate")
    tasks=[]
    for r in requirements:
        tid=hashlib.sha256((candidate+"|"+r["requirement"]).encode()).hexdigest()[:20]
        tasks.append({
            "task_id":tid,"candidate_name":candidate,"action_packet_id":packet.get("action_packet_id"),
            "requirement":r["requirement"],"guidance":r["guidance"],"source_capability":r["source"],
            "status":"research_required","created_at":time.time(),
            "external_send_allowed":False,"financial_action_allowed":False,"credential_access_allowed":False,"deployment_allowed":False,
            "research_contract":[
                "Use observable, attributable sources only.",
                "Do not invent URLs, quotes, prices, buyers, dates, or evidence.",
                "Record source identity, claim, observation date, and confidence.",
                "Prefer current primary or authoritative sources when available.",
                "Use independent corroboration for material claims when practical.",
                "Research only; do not contact prospects, purchase services, deploy, or transact.",
            ],
        })
    return tasks

def research_docs():
    if not RESEARCH_DIR.exists():return []
    out=[]
    for p in sorted(RESEARCH_DIR.glob("*.json"),key=lambda x:x.stat().st_mtime,reverse=True)[:300]:
        x=load(p,None)
        if isinstance(x,dict):out.append((p,x,json.dumps(x,default=str).lower()))
    return out

def validate_tasks(queue):
    docs=research_docs();completed=0
    for task in queue.get("tasks",[]):
        if not isinstance(task,dict) or task.get("status")!="research_required":continue
        candidate=str(task.get("candidate_name","")).lower()
        requirement=slug(task.get("requirement"))
        terms=[t for t in requirement.split("_") if t]
        matches=[]
        for p,x,text in docs:
            hits=sum(1 for t in terms if t in text)
            if hits < max(1,len(terms)//2):continue
            attribution=any(k in text for k in ('"url"','"source"','"sources"','"publisher"','"domain"','"retrieved_at"','"observed_at"'))
            if not attribution:continue
            candidate_hit=(candidate and candidate in text)
            if not candidate_hit and matches:continue
            matches.append({"path":str(p.relative_to(ROOT)),"observed_at":p.stat().st_mtime})
            if len(matches)>=3:break
        if matches:
            task["status"]="observed";task["observed_at"]=time.time();task["evidence_artifacts"]=matches
            completed+=1
            emit("evidence_observed",task_id=task.get("task_id"),requirement=requirement,matches=matches)
    return completed

def cycle():
    packet=latest_action_packet()
    q=load(QUEUE,{"tasks":[]})
    tasks=q.get("tasks")
    if not isinstance(tasks,list):tasks=[]
    q["tasks"]=tasks
    created=[]
    if packet:
        existing={t.get("task_id") for t in tasks if isinstance(t,dict)}
        for task in build_tasks(packet,requirements_from_packet(packet)):
            if task["task_id"] not in existing:
                tasks.append(task);created.append(task);existing.add(task["task_id"])
                emit("evidence_task_created",task_id=task["task_id"],requirement=task["requirement"],candidate=task["candidate_name"])
    observed=validate_tasks(q)
    q["tasks"]=tasks[-200:]
    atomic(QUEUE,q)
    state={
        "running":True,"healthy":True,"last_cycle_unix":time.time(),
        "latest_candidate":packet.get("candidate_name") if packet else None,
        "created_count":len(created),"observed_this_cycle":observed,
        "task_summary":{
            "total":len(tasks),
            "research_required":sum(1 for t in tasks if isinstance(t,dict) and t.get("status")=="research_required"),
            "observed":sum(1 for t in tasks if isinstance(t,dict) and t.get("status")=="observed"),
        },
        "latest_tasks":tasks[-10:],
    }
    atomic(STATE,state);return state

def run():
    interval=max(120,int(os.getenv("COMPANYOS_EVIDENCE_ACQUISITION_INTERVAL_SECONDS","300")))
    while not STOP.exists():
        try:cycle()
        except Exception as exc:
            atomic(STATE,{"running":True,"healthy":False,"last_cycle_unix":time.time(),"error":repr(exc)})
            emit("cycle_error",error=repr(exc))
        time.sleep(interval)

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser();a.add_argument("command",nargs="?",default="run",choices=("run","once","status","queue"));cmd=a.parse_args().command
    if cmd=="run":run()
    elif cmd=="once":print(json.dumps(cycle(),indent=2,sort_keys=True,default=str))
    elif cmd=="queue":print(json.dumps(load(QUEUE,{"tasks":[]}),indent=2,sort_keys=True,default=str))
    else:print(json.dumps(load(STATE,{"status":"not_run"}),indent=2,sort_keys=True,default=str))
