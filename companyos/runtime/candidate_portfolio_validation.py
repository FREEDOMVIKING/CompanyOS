from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from companyos.runtime import multi_provider_research_pipeline as mpr
from companyos.runtime import profit_opportunity_engine as poe
from companyos.runtime import provider_connector_router as pcr

RT=Path.home()/".companyos_runtime"
STATE=RT/"candidate_portfolio_validation_state.json"
HISTORY=RT/"candidate_portfolio_validation_history.jsonl"
EXPERIMENT_QUEUE=RT/"validation_experiment_queue.json"
EVIDENCE_QUEUE=RT/"evidence_acquisition_queue.json"
ARTIFACT_DIR=RT/"canonical_research_outputs"

VALIDATION_REQUIREMENTS=(
    "buyer_demand",
    "pricing",
    "provenance",
    "corroboration",
    "competition",
)

REQUIREMENT_GUIDANCE={
    "buyer_demand":"Find observable buyer/customer demand signals, adoption evidence, usage, purchase intent, or credible case studies.",
    "pricing":"Find observable market pricing, fees, subscriptions, quotes, or comparable price points.",
    "provenance":"Verify named source identity and trace the claim to an attributable primary or clearly identified source.",
    "corroboration":"Find an independent source that materially corroborates the commercial claim.",
    "competition":"Identify direct competitors, substitutes, alternatives, and visible commercial positioning.",
}


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


def append_history(obj:dict[str,Any]):
    HISTORY.parent.mkdir(parents=True,exist_ok=True)
    with HISTORY.open("a",encoding="utf-8") as f:
        f.write(json.dumps(obj,sort_keys=True,default=str)+"\n")


def num(v:Any,default:float=0.0)->float:
    try:
        return float(v)
    except Exception:
        return default


def clamp(v:Any)->float:
    return max(0.0,min(100.0,num(v)))


def normalize_category(value:Any)->str:
    x=str(value or "unknown").strip().lower()
    return x or "unknown"


def payload_coverage(payload:dict[str,Any])->float:
    return max(0.0,min(1.0,num(payload.get("observed_evidence_coverage"),0.0)))


def payload_critical_coverage(payload:dict[str,Any])->float:
    return max(0.0,min(1.0,num(payload.get("critical_evidence_coverage"),0.0)))


def portfolio_score(op:poe.Opportunity)->float:
    payload=op.payload if isinstance(op.payload,dict) else {}
    coverage=payload_coverage(payload)*100.0
    critical=payload_critical_coverage(payload)*100.0
    value=(
        0.62*clamp(op.score)
        +0.14*clamp(op.evidence_quality)
        +0.08*coverage
        +0.08*critical
        +0.08*clamp(op.readiness)
    )
    return round(clamp(value),2)


def lane(op:poe.Opportunity)->str:
    payload=op.payload if isinstance(op.payload,dict) else {}
    decision_ready=bool(payload.get("decision_ready",False))
    decision_status=str(payload.get("decision_status") or "").strip().lower()
    coverage=payload_coverage(payload)
    critical=payload_critical_coverage(payload)

    if (
        decision_ready
        and decision_status=="promote_to_guarded_execution"
        and coverage>=0.80
        and critical>=1.0
        and op.expected_profit>0
        and op.probability>0
    ):
        return "guarded_execution_ready"
    if op.score>=30 or op.evidence_count>0 or op.evidence_quality>0:
        return "validate_now"
    return "research_watch"


def candidate_record(op:poe.Opportunity)->dict[str,Any]:
    payload=op.payload if isinstance(op.payload,dict) else {}
    missing=payload.get("missing_evidence_requirements")
    if not isinstance(missing,list):
        missing=[]

    return {
        "id":op.id,
        "name":op.name,
        "mechanism":op.mechanism,
        "category":op.category,
        "source":op.source,
        "engine_score":op.score,
        "portfolio_score":portfolio_score(op),
        "lane":lane(op),
        "expected_profit":op.expected_profit,
        "probability":op.probability,
        "readiness":op.readiness,
        "evidence_count":op.evidence_count,
        "evidence_quality":op.evidence_quality,
        "coverage":payload_coverage(payload),
        "critical_coverage":payload_critical_coverage(payload),
        "missing_requirements":[
            str(x) for x in missing
            if str(x) in VALIDATION_REQUIREMENTS
        ],
        "next_action":op.next_action,
        "payload":payload,
    }


def select_portfolio(max_candidates:int=3)->list[dict[str,Any]]:
    limit=max(1,min(8,int(max_candidates)))
    records=[candidate_record(op) for op in poe.discover()]
    records.sort(
        key=lambda x:(
            -float(x["portfolio_score"]),
            -float(x["engine_score"]),
            x["name"].lower(),
        )
    )

    selected=[]
    used_ids=set()
    used_categories=set()

    for row in records:
        category=normalize_category(row.get("category"))
        if category in used_categories:
            continue
        selected.append(row)
        used_ids.add(row["id"])
        used_categories.add(category)
        if len(selected)>=limit:
            return selected

    for row in records:
        if row["id"] in used_ids:
            continue
        selected.append(row)
        used_ids.add(row["id"])
        if len(selected)>=limit:
            break

    return selected


def validation_requirement(candidate:dict[str,Any])->str:
    missing=[
        str(x) for x in candidate.get("missing_requirements") or []
        if str(x) in VALIDATION_REQUIREMENTS
    ]
    for req in VALIDATION_REQUIREMENTS:
        if req in missing:
            return req
    if candidate.get("lane")=="guarded_execution_ready":
        return "buyer_demand"
    if num(candidate.get("probability"),0)<=0:
        return "buyer_demand"
    if num(candidate.get("expected_profit"),0)<=0:
        return "pricing"
    return "competition"


def experiment_for(candidate:dict[str,Any])->dict[str,Any]:
    requirement=validation_requirement(candidate)
    payload=candidate.get("payload") if isinstance(candidate.get("payload"),dict) else {}
    guidance=REQUIREMENT_GUIDANCE[requirement]
    query=mpr._query(
        str(candidate.get("name") or ""),
        payload,
        requirement,
        guidance,
    )

    fingerprint=hashlib.sha256(
        (
            str(candidate.get("id") or candidate.get("name") or "")
            +"|"+requirement+"|v69.34"
        ).encode("utf-8")
    ).hexdigest()[:24]

    return {
        "experiment_id":fingerprint,
        "candidate_id":candidate.get("id"),
        "candidate_name":candidate.get("name"),
        "portfolio_score":candidate.get("portfolio_score"),
        "engine_score":candidate.get("engine_score"),
        "lane":candidate.get("lane"),
        "requirement":requirement,
        "experiment_type":"read_only_public_evidence_validation",
        "hypothesis":(
            f"Attributable public evidence can materially validate "
            f"{requirement.replace('_',' ')} for this commercial candidate."
        ),
        "query":query,
        "guidance":guidance,
        "success_criteria":[
            "At least two candidate-relevant attributable result rows.",
            "At least two distinct result URLs.",
            "The evidence is persisted with source identity and observation time.",
        ],
        "failure_criteria":[
            "Fewer than two candidate-relevant attributable result rows.",
            "Search sources are unavailable or return no candidate-relevant evidence.",
        ],
        "max_cost_usd":0.0,
        "external_message_allowed":False,
        "financial_action_allowed":False,
        "deployment_allowed":False,
        "account_creation_allowed":False,
        "credential_creation_allowed":False,
        "status":"planned",
        "portfolio_active":True,
        "created_at_unix":time.time(),
        "updated_at_unix":time.time(),
    }


def ensure_experiments(
    queue:dict[str,Any],
    selected:list[dict[str,Any]],
)->int:
    experiments=queue.get("experiments")
    if not isinstance(experiments,list):
        experiments=[]
        queue["experiments"]=experiments

    for row in experiments:
        if isinstance(row,dict):
            row["portfolio_active"]=False

    by_id={
        str(x.get("experiment_id") or ""):x
        for x in experiments
        if isinstance(x,dict)
    }

    created=0
    for candidate in selected:
        experiment=experiment_for(candidate)
        eid=experiment["experiment_id"]
        existing=by_id.get(eid)
        if existing:
            existing["portfolio_active"]=True
            existing["portfolio_score"]=candidate.get("portfolio_score")
            existing["engine_score"]=candidate.get("engine_score")
            existing["lane"]=candidate.get("lane")
            existing["updated_at_unix"]=time.time()
            continue
        experiments.append(experiment)
        by_id[eid]=experiment
        created+=1

    queue["experiments"]=experiments[-200:]
    return created


def _normalized_result_rows(result:dict[str,Any])->list[dict[str,Any]]:
    provider=str(result.get("provider") or "unknown")
    out=[]
    for row in result.get("results") or []:
        if not isinstance(row,dict):
            continue
        out.append({
            "source":row.get("source") or provider,
            "publisher":row.get("source") or provider,
            "url":row.get("url"),
            "title":row.get("title") or row.get("name") or "",
            "summary":row.get("content") or row.get("description") or row.get("summary") or "",
            "metadata":row.get("metadata") if isinstance(row.get("metadata"),dict) else {},
            "observed_at":time.time(),
            "evidence_method":"v69_34_read_only_validation_experiment",
            "research_provider":provider,
        })
    return out


def _candidate_by_name(
    selected:list[dict[str,Any]],
    name:str,
)->dict[str,Any]|None:
    for row in selected:
        if str(row.get("name") or "")==name:
            return row
    return None


def _valid_rows(
    candidate:dict[str,Any],
    requirement:str,
    rows:list[dict[str,Any]],
)->list[dict[str,Any]]:
    payload=candidate.get("payload") if isinstance(candidate.get("payload"),dict) else {}
    anchors=mpr._anchors(str(candidate.get("name") or ""),payload)
    return [
        row for row in rows
        if mpr._row_valid(row,anchors,requirement)
    ]


def _attach_evidence(
    candidate:dict[str,Any],
    requirement:str,
    artifact:Path,
):
    queue=load(EVIDENCE_QUEUE,{"tasks":[]})
    if not isinstance(queue,dict):
        queue={"tasks":[]}
    tasks=queue.get("tasks")
    if not isinstance(tasks,list):
        tasks=[]
        queue["tasks"]=tasks

    name=str(candidate.get("name") or "")
    task=None
    for row in tasks:
        if (
            isinstance(row,dict)
            and str(row.get("candidate_name") or "")==name
            and str(row.get("requirement") or "")==requirement
        ):
            task=row
            break

    if task is None:
        task_id=hashlib.sha256(
            (name+"|"+requirement).encode("utf-8")
        ).hexdigest()[:20]
        task={
            "task_id":task_id,
            "candidate_name":name,
            "action_packet_id":None,
            "requirement":requirement,
            "guidance":REQUIREMENT_GUIDANCE[requirement],
            "source_capability":"candidate_portfolio_validation_v69_34",
            "status":"research_required",
            "created_at":time.time(),
            "external_send_allowed":False,
            "financial_action_allowed":False,
            "credential_access_allowed":False,
            "deployment_allowed":False,
        }
        tasks.append(task)

    artifacts=task.get("evidence_artifacts")
    if not isinstance(artifacts,list):
        artifacts=[]

    existing_paths={
        str(x.get("path") if isinstance(x,dict) else x)
        for x in artifacts
    }
    if str(artifact) not in existing_paths:
        artifacts.append({
            "path":str(artifact),
            "source":"candidate_portfolio_validation_v69_34",
            "observed_at":time.time(),
        })

    task["evidence_artifacts"]=artifacts[-20:]
    task["status"]="observed"
    task["observed_at"]=time.time()
    task["validated_by"]="candidate_portfolio_validation_v69_34"
    queue["tasks"]=tasks[-400:]
    atomic(EVIDENCE_QUEUE,queue)


def execute_experiment(
    experiment:dict[str,Any],
    candidate:dict[str,Any],
)->dict[str,Any]:
    requirement=str(experiment.get("requirement") or "")
    query=str(experiment.get("query") or "").strip()

    if requirement not in VALIDATION_REQUIREMENTS or not query:
        experiment["status"]="invalid"
        experiment["updated_at_unix"]=time.time()
        return {
            "status":"invalid",
            "experiment_id":experiment.get("experiment_id"),
        }

    try:
        result=pcr.search_web(query,max_results=8)
        rows=_normalized_result_rows(result)
        valid=_valid_rows(candidate,requirement,rows)
        distinct_urls={
            str(x.get("url") or "").strip()
            for x in valid
            if str(x.get("url") or "").strip()
        }

        ARTIFACT_DIR.mkdir(parents=True,exist_ok=True)
        artifact=ARTIFACT_DIR/(
            "validation_experiment_v69_34_"
            +str(experiment["experiment_id"])
            +"_"+str(int(time.time()*1000))
            +".json"
        )

        passed=len(valid)>=2 and len(distinct_urls)>=2
        payload={
            "schema":"companyos.validation_experiment.v69_34",
            "created_at_unix":time.time(),
            "experiment_id":experiment["experiment_id"],
            "candidate_name":candidate.get("name"),
            "requirement":requirement,
            "query":query,
            "provider":result.get("provider"),
            "provider_attempts":result.get("attempts") or [],
            "source_rows":valid,
            "raw_result_count":len(rows),
            "candidate_relevant_result_count":len(valid),
            "distinct_url_count":len(distinct_urls),
            "result":"pass" if passed else "inconclusive",
            "external_messages_sent":False,
            "financial_actions_performed":False,
            "deployments_performed":False,
            "economic_values_modified":False,
        }
        atomic(artifact,payload)

        experiment["status"]="passed" if passed else "inconclusive"
        experiment["last_result"]=payload["result"]
        experiment["artifact"]=str(artifact)
        experiment["candidate_relevant_result_count"]=len(valid)
        experiment["distinct_url_count"]=len(distinct_urls)
        experiment["provider"]=result.get("provider")
        experiment["last_attempt_unix"]=time.time()
        experiment["next_retry_unix"]=(
            0.0 if passed else time.time()+24*3600
        )
        experiment["updated_at_unix"]=time.time()

        if passed:
            _attach_evidence(candidate,requirement,artifact)

        return {
            "experiment_id":experiment["experiment_id"],
            "candidate_name":candidate.get("name"),
            "requirement":requirement,
            "status":experiment["status"],
            "artifact":str(artifact),
            "candidate_relevant_result_count":len(valid),
            "distinct_url_count":len(distinct_urls),
            "provider":result.get("provider"),
        }
    except Exception as exc:
        experiment["status"]="inconclusive"
        experiment["last_error"]=f"{type(exc).__name__}:{str(exc)[:800]}"
        experiment["last_attempt_unix"]=time.time()
        experiment["next_retry_unix"]=time.time()+6*3600
        experiment["updated_at_unix"]=time.time()
        return {
            "experiment_id":experiment.get("experiment_id"),
            "candidate_name":candidate.get("name"),
            "requirement":requirement,
            "status":"inconclusive",
            "error":experiment["last_error"],
        }


def cycle(
    max_candidates:int=3,
    execute_limit:int=1,
)->dict[str,Any]:
    selected=select_portfolio(max_candidates=max_candidates)

    queue=load(EXPERIMENT_QUEUE,{"experiments":[]})
    if not isinstance(queue,dict):
        queue={"experiments":[]}

    created=ensure_experiments(queue,selected)
    experiments=queue.get("experiments")
    if not isinstance(experiments,list):
        experiments=[]
        queue["experiments"]=experiments

    now=time.time()
    executable=[
        x for x in experiments
        if isinstance(x,dict)
        and x.get("portfolio_active") is True
        and (
            x.get("status")=="planned"
            or (
                x.get("status")=="inconclusive"
                and num(x.get("next_retry_unix"),0)<=now
            )
        )
    ]
    executable.sort(
        key=lambda x:(
            -num(x.get("portfolio_score"),0),
            num(x.get("created_at_unix"),0),
        )
    )

    outcomes=[]
    for experiment in executable[:max(0,int(execute_limit))]:
        candidate=_candidate_by_name(
            selected,
            str(experiment.get("candidate_name") or ""),
        )
        if candidate is None:
            continue
        outcomes.append(execute_experiment(experiment,candidate))

    queue["experiments"]=experiments[-200:]
    queue["updated_at_unix"]=time.time()
    atomic(EXPERIMENT_QUEUE,queue)

    portfolio=[
        {
            k:v for k,v in row.items()
            if k!="payload"
        }
        for row in selected
    ]

    state={
        "schema":"companyos.candidate_portfolio_validation.v69_34",
        "running":True,
        "healthy":True,
        "last_cycle_unix":time.time(),
        "portfolio_size":len(portfolio),
        "portfolio":portfolio,
        "experiments_created":created,
        "experiments_executed":len(outcomes),
        "experiment_outcomes":outcomes,
        "active_experiment_count":sum(
            1 for x in experiments
            if isinstance(x,dict) and x.get("portfolio_active") is True
        ),
        "passed_experiment_count":sum(
            1 for x in experiments
            if isinstance(x,dict) and x.get("status")=="passed"
        ),
        "inconclusive_experiment_count":sum(
            1 for x in experiments
            if isinstance(x,dict) and x.get("status")=="inconclusive"
        ),
        "selection_objective":"diversified_risk_adjusted_profit_validation",
        "external_messages_sent":False,
        "financial_actions_performed":False,
        "deployments_performed":False,
        "account_creation_performed":False,
        "public_key_harvesting_performed":False,
        "economic_values_auto_modified":False,
    }

    atomic(STATE,state)
    append_history({
        "ts":state["last_cycle_unix"],
        "portfolio_size":state["portfolio_size"],
        "selected":[
            {
                "name":x.get("name"),
                "category":x.get("category"),
                "portfolio_score":x.get("portfolio_score"),
                "lane":x.get("lane"),
            }
            for x in portfolio
        ],
        "experiments_executed":state["experiments_executed"],
        "experiment_outcomes":outcomes,
    })
    return state


if __name__=="__main__":
    import argparse

    parser=argparse.ArgumentParser()
    parser.add_argument(
        "command",
        nargs="?",
        default="once",
        choices=("once","status","queue"),
    )
    parser.add_argument("--max-candidates",type=int,default=3)
    parser.add_argument("--execute-limit",type=int,default=1)
    args=parser.parse_args()

    if args.command=="once":
        print(json.dumps(
            cycle(
                max_candidates=args.max_candidates,
                execute_limit=args.execute_limit,
            ),
            indent=2,
            sort_keys=True,
            default=str,
        ))
    elif args.command=="queue":
        print(json.dumps(
            load(EXPERIMENT_QUEUE,{"experiments":[]}),
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
