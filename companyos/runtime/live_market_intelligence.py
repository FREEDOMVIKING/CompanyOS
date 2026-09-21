from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any

from companyos.runtime import autonomous_evidence_acquisition as aea
from companyos.runtime import multi_provider_research_pipeline as mpr
from companyos.runtime import provider_connector_router as pcr

ROOT=Path.home()/"companyos"
RT=Path.home()/".companyos_runtime"
STATE=RT/"live_market_intelligence_state.json"
SCAN_STATE=RT/"live_market_scan_state.json"
QUEUE=RT/"evidence_acquisition_queue.json"
CANDIDATES=RT/"profit_first_candidates"
RESEARCH=RT/"canonical_research_outputs"
STOP=RT/"STOP_CONTINUOUS"

TOPICS=[
    "small business workflow automation recurring revenue",
    "field service operations software pain points",
    "construction operations automation software",
    "logistics operations workflow software",
    "ecommerce operations automation pain points",
    "B2B compliance workflow software",
    "sales operations automation small business",
    "customer support workflow automation SMB",
    "developer productivity workflow software",
    "property management operations automation",
    "manufacturing operations software pain points",
    "healthcare administrative workflow automation",
    "data enrichment API business demand",
    "local service business scheduling automation",
    "procurement workflow software pain points",
    "finance back office automation small business",
]

# COMPANYOS_V69_33_EVIDENCE_GAP_ACCELERATION
# Preserve the V69.32 public contract: ensure_tasks() defaults to exactly
# buyer_demand, pricing, and competition.  The live V69.33 cycle opts into
# the expanded requirement set explicitly.
DEFAULT_REQUIREMENTS=("buyer_demand","pricing","competition")
EVIDENCE_GAP_REQUIREMENTS=(
    "buyer_demand",
    "pricing",
    "provenance",
    "corroboration",
    "competition",
)


def load(path:Path,default:Any):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def atomic(path:Path,obj:Any):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(
        json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def slug(v:Any)->str:
    s=re.sub(r"[^a-z0-9]+","_",str(v or "").lower()).strip("_")
    return s[:80] or "candidate"


def candidate_name(payload:dict[str,Any],path:Path)->str:
    return str(
        payload.get("name")
        or payload.get("candidate_name")
        or payload.get("venture_name")
        or path.stem
    )


def candidate_rows()->list[dict[str,Any]]:
    rows=[]
    if not CANDIDATES.exists():
        return rows

    paths=list(CANDIDATES.glob("*.json"))
    base_paths=[p for p in paths if not p.name.startswith("enriched_")]
    if base_paths:
        paths=base_paths

    for path in paths:
        payload=load(path,None)
        if not isinstance(payload,dict):
            continue
        name=candidate_name(payload,path)
        if not name.strip():
            continue

        evidence_conf=float(payload.get("evidence_confidence") or 0)
        demand=float(payload.get("market_demand") or 0)
        profit=float(payload.get("expected_profit") or 0)
        success=float(payload.get("probability_of_success") or payload.get("probability") or 0)
        needs=bool(payload.get("needs_enrichment",False))
        evidence_count=int(payload.get("observed_evidence_count") or 0)
        evidence_coverage=float(payload.get("observed_evidence_coverage") or 0)
        critical_coverage=float(payload.get("critical_evidence_coverage") or 0)

        rows.append({
            "name":name,
            "path":path,
            "payload":payload,
            "priority":(
                (50 if needs else 0)
                +(100-evidence_conf)*0.7
                +demand*0.2
                +profit*0.2
                +success*0.1
                +(1.0-evidence_coverage)*60.0
                +(1.0-critical_coverage)*40.0
                -evidence_count*2
            ),
        })

    rows.sort(key=lambda x:(-x["priority"],x["name"].lower()))
    return rows


def selected_candidates(max_candidates:int=4)->list[dict[str,Any]]:
    rows=candidate_rows()
    latest=aea.latest_action_packet()
    latest_name=str((latest or {}).get("candidate_name") or "").strip()

    selected=[]
    used=set()

    if latest_name:
        for row in rows:
            if row["name"]==latest_name:
                selected.append(row)
                used.add(row["name"])
                break

    for row in rows:
        if row["name"] in used:
            continue
        selected.append(row)
        used.add(row["name"])
        if len(selected)>=max(1,int(max_candidates)):
            break

    return selected[:max(1,int(max_candidates))]


def ensure_tasks(
    queue:dict[str,Any],
    candidates:list[dict[str,Any]],
    requirements:tuple[str,...]=DEFAULT_REQUIREMENTS,
)->int:
    tasks=queue.get("tasks")
    if not isinstance(tasks,list):
        tasks=[]
        queue["tasks"]=tasks

    existing={
        (str(t.get("candidate_name") or ""),str(t.get("requirement") or ""))
        for t in tasks if isinstance(t,dict)
    }
    created=0

    for row in candidates:
        name=row["name"]
        for requirement in requirements:
            key=(name,requirement)
            if key in existing:
                continue

            task_id=hashlib.sha256(
                (name+"|"+requirement).encode("utf-8")
            ).hexdigest()[:20]

            tasks.append({
                "task_id":task_id,
                "candidate_name":name,
                "action_packet_id":None,
                "requirement":requirement,
                "guidance":aea.REQUIREMENTS.get(
                    requirement,
                    "Collect concrete attributable evidence."
                ),
                "source_capability":"live_market_intelligence_v69_32",
                "status":"research_required",
                "created_at":time.time(),
                "external_send_allowed":False,
                "financial_action_allowed":False,
                "credential_access_allowed":False,
                "deployment_allowed":False,
                "research_contract":[
                    "Use observable attributable sources only.",
                    "Do not invent URLs, quotes, prices, buyers, dates, or evidence.",
                    "Record source identity, claim, observation date, and confidence.",
                    "Research only; do not contact prospects, purchase, deploy, or transact.",
                ],
            })
            existing.add(key)
            created+=1

    return created


def _scan_index()->int:
    state=load(SCAN_STATE,{})
    try:
        return int(state.get("next_index") or 0)
    except Exception:
        return 0


def market_scan(max_topics:int=4,results_per_topic:int=6)->dict[str,Any]:
    RESEARCH.mkdir(parents=True,exist_ok=True)

    start=_scan_index()
    chosen=[
        TOPICS[(start+i)%len(TOPICS)]
        for i in range(max(1,min(int(max_topics),len(TOPICS))))
    ]

    rows=[]
    attempts=[]
    for topic in chosen:
        try:
            result=pcr.search_web(topic,max_results=max(1,min(10,int(results_per_topic))))
            attempts.append({
                "topic":topic,
                "provider":result.get("provider"),
                "result_count":int(result.get("result_count") or 0),
                "attempts":result.get("attempts") or [],
            })
            for item in result.get("results") or []:
                if not isinstance(item,dict):
                    continue
                url=str(item.get("url") or "").strip()
                title=str(item.get("title") or item.get("name") or "").strip()
                if not url and not title:
                    continue
                rows.append({
                    "source":item.get("source") or result.get("provider"),
                    "publisher":item.get("source") or result.get("provider"),
                    "url":url,
                    "title":title,
                    "summary":item.get("content") or item.get("description") or item.get("summary") or "",
                    "metadata":item.get("metadata") if isinstance(item.get("metadata"),dict) else {},
                    "topic":topic,
                    "observed_at":time.time(),
                })
        except Exception as exc:
            attempts.append({
                "topic":topic,
                "provider":None,
                "result_count":0,
                "error":f"{type(exc).__name__}:{str(exc)[:500]}",
            })

    dedup=[]
    seen=set()
    for row in rows:
        key=(row.get("url") or row.get("title") or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        dedup.append(row)

    stamp=int(time.time()*1000)
    artifact=RESEARCH/f"live_market_scan_v69_32_{stamp}.json"
    payload={
        "schema":"companyos.live_market_scan.v69_32",
        "created_at_unix":time.time(),
        "topics":chosen,
        "source_rows":dedup,
        "source_row_count":len(dedup),
        "provider_attempts":attempts,
        "research_only":True,
        "external_action_performed":False,
        "financial_action_performed":False,
        "deployment_performed":False,
    }
    atomic(artifact,payload)

    next_index=(start+len(chosen))%len(TOPICS)
    state={
        "schema":"companyos.live_market_scan_state.v69_32",
        "last_cycle_unix":time.time(),
        "next_index":next_index,
        "topics_scanned":chosen,
        "source_row_count":len(dedup),
        "artifact":str(artifact),
        "provider_attempts":attempts,
        "healthy":True,
    }
    atomic(SCAN_STATE,state)
    return state


def _update_candidate_evidence_metadata(
    selected:list[dict[str,Any]],
    queue:dict[str,Any],
)->list[dict[str,Any]]:
    tasks=queue.get("tasks") if isinstance(queue.get("tasks"),list) else []
    updates=[]

    for row in selected:
        name=row["name"]
        relevant=[
            t for t in tasks
            if isinstance(t,dict)
            and str(t.get("candidate_name") or "")==name
        ]
        observed=[t for t in relevant if t.get("status")=="observed"]
        requirements=sorted({
            str(t.get("requirement") or "")
            for t in observed
            if t.get("requirement")
        })

        payload=load(row["path"],{})
        if not isinstance(payload,dict):
            continue

        payload["observed_evidence_count"]=len(observed)
        payload["observed_evidence_requirements"]=requirements
        payload["observed_evidence_coverage"]=round(
            len(observed)/len(relevant),4
        ) if relevant else 0.0
        payload["live_market_intelligence_updated_at_unix"]=time.time()

        atomic(row["path"],payload)
        updates.append({
            "candidate":name,
            "observed":len(observed),
            "total_tasks":len(relevant),
            "requirements":requirements,
        })

    return updates


def cycle(max_candidates:int=4,max_tasks:int=8)->dict[str,Any]:
    scan=market_scan(
        max_topics=int(os.getenv("COMPANYOS_MARKET_SCAN_TOPICS_PER_CYCLE","4")),
        results_per_topic=int(os.getenv("COMPANYOS_MARKET_SCAN_RESULTS_PER_TOPIC","6")),
    )

    selected=selected_candidates(max_candidates=max_candidates)

    queue=load(QUEUE,{"tasks":[]})
    if not isinstance(queue,dict):
        queue={"tasks":[]}

    created=ensure_tasks(
        queue,
        selected,
        requirements=EVIDENCE_GAP_REQUIREMENTS,
    )

    provider_research=mpr.cycle(
        queue=queue,
        persist_queue=False,
        max_tasks=max(1,min(12,int(max_tasks))),
    )

    invalidated=aea.reconcile_observed_tasks(queue)
    observed=aea.validate_tasks(queue)

    tasks=queue.get("tasks")
    if not isinstance(tasks,list):
        tasks=[]
    queue["tasks"]=tasks[-300:]
    atomic(QUEUE,queue)

    candidate_updates=_update_candidate_evidence_metadata(selected,queue)

    rescoring=None
    try:
        from companyos.runtime import evidence_coverage_rescoring as ecr
        rescoring=ecr.cycle(max_candidates=50)
    except Exception as exc:
        rescoring={
            "healthy":False,
            "error":f"{type(exc).__name__}:{str(exc)[:800]}",
        }

    # COMPANYOS_V69_34_PORTFOLIO_VALIDATION
    portfolio_validation=None
    try:
        from companyos.runtime import candidate_portfolio_validation as cpv
        portfolio_validation=cpv.cycle(
            max_candidates=int(os.getenv("COMPANYOS_PORTFOLIO_SIZE","3")),
            execute_limit=int(os.getenv("COMPANYOS_VALIDATION_EXPERIMENTS_PER_CYCLE","1")),
        )
    except Exception as exc:
        portfolio_validation={
            "healthy":False,
            "error":f"{type(exc).__name__}:{str(exc)[:800]}",
        }

    enrichment=None
    try:
        from companyos.runtime.candidate_enrichment_bridge import refresh_enrichments
        enrichment=refresh_enrichments(max_age_hours=168)
    except Exception as exc:
        enrichment={
            "healthy":False,
            "error":f"{type(exc).__name__}:{str(exc)[:800]}",
        }

    decision=None
    try:
        from companyos.runtime import evidence_decision_closure as edc
        decision=edc.cycle()
    except Exception as exc:
        decision={
            "healthy":False,
            "error":f"{type(exc).__name__}:{str(exc)[:800]}",
        }

    state={
        "schema":"companyos.live_market_intelligence.v69_32",
        "running":True,
        "healthy":True,
        "last_cycle_unix":time.time(),
        "market_scan":scan,
        "selected_candidates":[x["name"] for x in selected],
        "evidence_tasks_created":created,
        "provider_research":provider_research,
        "observed_this_cycle":observed,
        "invalidated_this_cycle":invalidated,
        "candidate_updates":candidate_updates,
        "evidence_rescoring":rescoring,
        "candidate_portfolio_validation":portfolio_validation,
        "candidate_enrichment":enrichment,
        "decision_closure":decision,
        "queue_summary":{
            "total":len(tasks),
            "research_required":sum(
                1 for t in tasks
                if isinstance(t,dict) and t.get("status")=="research_required"
            ),
            "observed":sum(
                1 for t in tasks
                if isinstance(t,dict) and t.get("status")=="observed"
            ),
        },
        "external_messages_sent":False,
        "financial_actions_performed":False,
        "deployments_performed":False,
        "account_creation_performed":False,
        "public_key_harvesting_performed":False,
    }
    atomic(STATE,state)
    return state


def run():
    interval=max(
        120,
        int(os.getenv("COMPANYOS_LIVE_MARKET_INTELLIGENCE_INTERVAL_SECONDS","300"))
    )
    while not STOP.exists():
        try:
            cycle(
                max_candidates=int(os.getenv("COMPANYOS_EVIDENCE_CANDIDATES_PER_CYCLE","4")),
                max_tasks=int(os.getenv("COMPANYOS_EVIDENCE_TASKS_PER_CYCLE","8")),
            )
        except Exception as exc:
            atomic(
                STATE,
                {
                    "schema":"companyos.live_market_intelligence.v69_32",
                    "running":True,
                    "healthy":False,
                    "last_cycle_unix":time.time(),
                    "error":f"{type(exc).__name__}:{str(exc)[:1200]}",
                },
            )
        time.sleep(interval)


if __name__=="__main__":
    import argparse

    parser=argparse.ArgumentParser()
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=("run","once","status","scan"),
    )
    parser.add_argument("--max-candidates",type=int,default=4)
    parser.add_argument("--max-tasks",type=int,default=8)
    args=parser.parse_args()

    if args.command=="run":
        run()
    elif args.command=="once":
        print(json.dumps(
            cycle(
                max_candidates=args.max_candidates,
                max_tasks=args.max_tasks,
            ),
            indent=2,
            sort_keys=True,
            default=str,
        ))
    elif args.command=="scan":
        print(json.dumps(
            market_scan(),
            indent=2,
            sort_keys=True,
            default=str,
        ))
    else:
        print(json.dumps(
            load(STATE,{"status":"not_run"}),
            indent=2,
            sort_keys=True,
            default=str,
        ))
