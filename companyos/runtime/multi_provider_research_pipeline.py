from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

from companyos.runtime import provider_connector_router as pcr
from companyos.runtime import targeted_public_evidence_research as base

RT=Path.home()/".companyos_runtime"
STATE=RT/"multi_provider_research_state.json"
HISTORY=RT/"multi_provider_research_history.jsonl"
QUEUE=RT/"evidence_acquisition_queue.json"
RESEARCH_DIR=RT/"canonical_research_outputs"

DEFAULT_DEFER_SECONDS=max(
    300,
    int(os.getenv("COMPANYOS_RESEARCH_DEFER_SECONDS","1200")),
)

REQUIREMENT_TERMS={
    "pricing":{"price","pricing","cost","costs","fee","fees","subscription","plan","paid","quote"},
    "buyer_demand":{"buyer","buyers","customer","customers","client","clients","demand","adoption","users","purchase"},
    "competition":{"competitor","competitors","competition","alternative","alternatives","substitute"},
    "provenance":{"source","publisher","author","official","owner"},
    "recency":{"updated","published","date","recent","2025","2026"},
    "authority":{"official","government","vendor","company","publisher"},
    "corroboration":{"source","sources","independent","report","study"},
    "relevance":{"customer","buyer","market","workflow","problem","service"},
    "traceability":{"source","url","published","updated"},
}

STOPWORDS={
    "about","after","against","business","candidate","company","customer","evidence",
    "first","from","into","market","more","other","research","service","software",
    "their","there","these","this","through","using","with","would",
    "regional","local","global","online","digital","platform",
}

# COMPANYOS_V69_32_LIVE_EVIDENCE_QUERY_BINDING

def load(path,default=None):
    if default is None:
        default={}
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default

def atomic(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(
        json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n",
        encoding="utf-8",
    )
    tmp.replace(path)

def append_history(obj):
    HISTORY.parent.mkdir(parents=True,exist_ok=True)
    with HISTORY.open("a",encoding="utf-8") as f:
        f.write(json.dumps(obj,sort_keys=True,default=str)+"\n")

def _norm(v):
    return re.sub(r"[^a-z0-9]+"," ",str(v or "").lower()).strip()

def _candidate(name):
    path,payload=base.candidate_payload(name)
    return path,payload if isinstance(payload,dict) else {}

def _anchors(name,payload):
    values=[
        name,
        payload.get("name"),
        payload.get("market"),
        payload.get("sector"),
        payload.get("target_customer"),
        payload.get("problem"),
        payload.get("offer"),
        payload.get("business_model"),
    ]
    out=set()
    for value in values:
        for token in re.findall(r"[a-z0-9]+",_norm(value)):
            if len(token)>=4 and token not in STOPWORDS:
                out.add(token)
    return out

def _query(name,payload,requirement,guidance):
    market=str(payload.get("market") or payload.get("sector") or "").strip()
    customer=str(payload.get("target_customer") or "").strip()
    problem=str(payload.get("problem") or "").strip()
    offer=str(payload.get("offer") or "").strip()
    business_model=str(payload.get("business_model") or "").strip()

    if requirement=="pricing":
        focus="pricing price cost subscription fee quote"
    elif requirement=="buyer_demand":
        focus="customers adoption demand buyers usage case study"
    elif requirement=="competition":
        focus="competitors alternatives substitutes pricing"
    elif requirement=="corroboration":
        focus="independent report study sources"
    else:
        focus=requirement.replace("_"," ")

    parts=[name,market,business_model,customer,problem,offer,focus]
    return " ".join(x for x in parts if x)[:500]

def _actual_evidence_text(row):
    return _norm(
        " ".join(
            str(row.get(k) or "")
            for k in ("title","content","description","summary","publisher","source")
        )
    )

def _row_valid(row,anchors,requirement):
    url=str(row.get("url") or "").strip()
    if not url.startswith(("http://","https://")):
        return False

    text=_actual_evidence_text(row)
    hits={a for a in anchors if a in text}
    required_anchor_hits=2 if len(anchors)>=3 else 1
    if len(hits)<required_anchor_hits:
        return False

    terms=REQUIREMENT_TERMS.get(requirement)
    if not terms:
        terms={x for x in requirement.split("_") if len(x)>=4}

    return any(term in text for term in terms)

def _normalize_rows(provider_result):
    provider=str(provider_result.get("provider") or "")
    out=[]
    for row in provider_result.get("results") or []:
        if not isinstance(row,dict):
            continue
        actual_source=str(row.get("source") or provider or "unknown")
        out.append({
            "source":actual_source,
            "publisher":actual_source,
            "url":row.get("url"),
            "title":row.get("title") or row.get("name") or "",
            "summary":row.get("content") or row.get("description") or row.get("summary") or "",
            "metadata":row.get("metadata") if isinstance(row.get("metadata"),dict) else {},
            "observed_at":time.time(),
            "evidence_method":"multi_provider_public_web_search",
            "research_provider":provider,
        })
    return out

def _persist_artifact(candidate,requirement,query,provider_result,rows):
    RESEARCH_DIR.mkdir(parents=True,exist_ok=True)
    safe=re.sub(r"[^a-z0-9]+","_",candidate.lower()).strip("_")[:80] or "candidate"
    path=RESEARCH_DIR/f"multi_provider_evidence_v69_28_{safe}_{requirement}_{int(time.time()*1000)}.json"

    payload={
        "schema":"companyos.multi_provider_evidence.v69_28",
        "candidate_name":candidate,
        "requirement":requirement,
        "search_query":query,
        "provider":provider_result.get("provider"),
        "provider_attempts":provider_result.get("attempts") or provider_result.get("provider_attempts") or [],
        "source_rows":rows,
        "source_row_count":len(rows),
        "filter_policy":{
            "minimum_candidate_anchor_hits_in_actual_result_text":"2_when_3plus_anchors_else_1",
            "requirement_term_required_in_actual_result_text":True,
            "query_text_not_counted_as_evidence":True,
            "invented_evidence_allowed":False,
        },
        "external_action_performed":False,
        "financial_action_performed":False,
        "deployment_performed":False,
        "created_at_unix":time.time(),
    }
    atomic(path,payload)
    return path

def _due(task,now):
    try:
        return float(task.get("research_deferred_until_unix") or 0.0)<=now
    except Exception:
        return True

def _candidate_diverse_tasks(tasks,max_tasks):
    ordered=sorted(
        tasks,
        key=lambda t:(
            float(t.get("provider_last_attempt_at_unix") or 0.0),
            float(t.get("created_at") or 0.0),
        ),
    )
    chosen=[]
    seen=set()

    for task in ordered:
        candidate=str(task.get("candidate_name") or "")
        if candidate in seen:
            continue
        chosen.append(task)
        seen.add(candidate)
        if len(chosen)>=max_tasks:
            return chosen

    for task in ordered:
        if task in chosen:
            continue
        chosen.append(task)
        if len(chosen)>=max_tasks:
            break

    return chosen

def _defer(task,reason,seconds=DEFAULT_DEFER_SECONDS):
    now=time.time()
    task["provider_last_attempt_at_unix"]=now
    task["research_deferred_until_unix"]=now+max(60,int(seconds))
    task["research_deferred_reason"]=reason
    task["global_runtime_blocked"]=False

def _research_task(task,web_providers):
    candidate=str(task.get("candidate_name") or "")
    requirement=str(task.get("requirement") or "")
    guidance=str(task.get("guidance") or "")
    path,payload=_candidate(candidate)

    task["provider_last_attempt_at_unix"]=time.time()
    task["global_runtime_blocked"]=False

    if not path or not payload:
        _defer(task,"candidate_payload_missing",3600)
        return {
            "candidate":candidate,
            "requirement":requirement,
            "status":"deferred",
            "reason":"candidate_payload_missing",
        }

    if not web_providers:
        _defer(task,"no_web_search_provider",DEFAULT_DEFER_SECONDS)
        return {
            "candidate":candidate,
            "requirement":requirement,
            "status":"deferred",
            "reason":"no_web_search_provider",
        }

    query=_query(candidate,payload,requirement,guidance)
    result=pcr.search_web(query,max_results=8)

    if int(result.get("result_count") or 0)<=0:
        _defer(task,"provider_returned_no_results",900)
        return {
            "candidate":candidate,
            "requirement":requirement,
            "status":"deferred",
            "reason":"provider_returned_no_results",
            "provider":result.get("provider"),
        }

    anchors=_anchors(candidate,payload)
    rows=[
        row for row in _normalize_rows(result)
        if _row_valid(row,anchors,requirement)
    ]

    artifact=_persist_artifact(
        candidate,
        requirement,
        query,
        result,
        rows,
    )

    task["provider_last_artifact"]=str(artifact)
    task["provider_last_name"]=result.get("provider")
    task["provider_last_valid_rows"]=len(rows)

    if not rows:
        _defer(task,"results_not_candidate_bound_or_requirement_specific",900)
        return {
            "candidate":candidate,
            "requirement":requirement,
            "status":"deferred",
            "reason":"results_not_candidate_bound_or_requirement_specific",
            "provider":result.get("provider"),
            "artifact":str(artifact),
        }

    task.pop("research_deferred_until_unix",None)
    task.pop("research_deferred_reason",None)

    return {
        "candidate":candidate,
        "requirement":requirement,
        "status":"evidence_artifact_created",
        "provider":result.get("provider"),
        "valid_rows":len(rows),
        "artifact":str(artifact),
    }

def internal_planning_smoke():
    return pcr.infer_text(
        "Return exactly the word READY. Do not use tools.",
        max_tokens=32,
    )

def cycle(queue=None,persist_queue=True,max_tasks=3):
    now=time.time()
    q=queue if isinstance(queue,dict) else load(QUEUE,{"tasks":[]})
    tasks=q.get("tasks")
    if not isinstance(tasks,list):
        tasks=[]
        q["tasks"]=tasks

    status=pcr.provider_status()
    caps=status.get("capabilities") or {}
    web_providers=list(caps.get("web_search") or [])
    inference_providers=list(caps.get("llm_inference") or [])
    public_code=list(caps.get("public_code_research") or [])

    pending=[
        t for t in tasks
        if isinstance(t,dict)
        and t.get("status")=="research_required"
        and _due(t,now)
    ]

    selected=_candidate_diverse_tasks(
        pending,
        max(1,min(8,int(max_tasks))),
    )

    outcomes=[]
    for task in selected:
        try:
            outcomes.append(_research_task(task,web_providers))
        except Exception as exc:
            _defer(task,f"provider_exception:{type(exc).__name__}",900)
            outcomes.append({
                "candidate":task.get("candidate_name"),
                "requirement":task.get("requirement"),
                "status":"deferred",
                "reason":f"{type(exc).__name__}:{str(exc)[:400]}",
            })

    if persist_queue:
        atomic(QUEUE,q)

    deferred=sum(1 for x in outcomes if x.get("status")=="deferred")
    created=sum(1 for x in outcomes if x.get("status")=="evidence_artifact_created")

    state={
        "schema":"companyos.multi_provider_research_pipeline.v69_28",
        "last_cycle_unix":time.time(),
        "healthy":True,
        "global_runtime_blocked":False,
        "candidate_rotation_enabled":True,
        "provider_capabilities":{
            "web_search":web_providers,
            "llm_inference":inference_providers,
            "public_code_research":public_code,
        },
        "pending_due_count":len(pending),
        "selected_task_count":len(selected),
        "evidence_artifacts_created":created,
        "deferred_task_count":deferred,
        "outcomes":outcomes,
        "external_messages_sent":False,
        "financial_actions_performed":False,
        "deployments_performed":False,
        "forced_promotion":False,
    }
    atomic(STATE,state)
    append_history(state)
    return state

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("command",nargs="?",default="once",choices=("once","status","smoke"))
    p.add_argument("--max-tasks",type=int,default=3)
    a=p.parse_args()

    if a.command=="once":
        print(json.dumps(cycle(max_tasks=a.max_tasks),indent=2,sort_keys=True))
    elif a.command=="smoke":
        print(json.dumps(internal_planning_smoke(),indent=2,sort_keys=True))
    else:
        print(json.dumps(load(STATE,{"status":"not_run"}),indent=2,sort_keys=True))
