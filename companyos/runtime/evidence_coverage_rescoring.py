from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

ROOT=Path.home()/"companyos"
RT=Path.home()/".companyos_runtime"
QUEUE=RT/"evidence_acquisition_queue.json"
CANDIDATES=RT/"profit_first_candidates"
STATE=RT/"evidence_coverage_rescoring_state.json"
HISTORY=RT/"evidence_coverage_rescoring_history.jsonl"

CORE_REQUIREMENTS=(
    "buyer_demand",
    "pricing",
    "competition",
    "provenance",
    "corroboration",
)

CRITICAL_REQUIREMENTS=(
    "buyer_demand",
    "pricing",
    "provenance",
    "corroboration",
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


def append_history(obj:dict[str,Any]):
    HISTORY.parent.mkdir(parents=True,exist_ok=True)
    with HISTORY.open("a",encoding="utf-8") as f:
        f.write(json.dumps(obj,sort_keys=True,default=str)+"\n")


def clamp(v:Any)->float:
    try:
        x=float(v)
    except Exception:
        x=0.0
    return max(0.0,min(100.0,x))


def candidate_name(payload:dict[str,Any],path:Path)->str:
    return str(
        payload.get("name")
        or payload.get("candidate_name")
        or payload.get("venture_name")
        or path.stem
    )


def candidate_files()->list[tuple[Path,dict[str,Any]]]:
    rows=[]
    if not CANDIDATES.exists():
        return rows
    for path in sorted(CANDIDATES.glob("*.json")):
        if path.name.startswith("enriched_"):
            continue
        payload=load(path,None)
        if isinstance(payload,dict):
            rows.append((path,payload))
    return rows


def tasks_for(name:str,queue:dict[str,Any])->list[dict[str,Any]]:
    tasks=queue.get("tasks")
    if not isinstance(tasks,list):
        return []
    return [
        t for t in tasks
        if isinstance(t,dict)
        and str(t.get("candidate_name") or "")==name
    ]


def _evidence_rows_from_artifact(path_value:Any)->list[dict[str,Any]]:
    if not path_value:
        return []
    path=Path(str(path_value))
    doc=load(path,None)
    if not isinstance(doc,dict):
        return []

    rows=[]
    for key in (
        "source_rows",
        "evidence_sources",
        "sources",
        "citations",
        "market_evidence",
        "observations",
    ):
        value=doc.get(key)
        if isinstance(value,list):
            rows.extend(x for x in value if isinstance(x,dict))
        elif isinstance(value,dict):
            rows.append(value)

    return rows


def evidence_metrics(name:str,queue:dict[str,Any],now:float|None=None)->dict[str,Any]:
    now=time.time() if now is None else float(now)
    tasks=tasks_for(name,queue)
    observed=[t for t in tasks if t.get("status")=="observed"]

    observed_reqs={
        str(t.get("requirement") or "")
        for t in observed
        if str(t.get("requirement") or "") in CORE_REQUIREMENTS
    }

    coverage=len(observed_reqs)/len(CORE_REQUIREMENTS)
    critical_observed=observed_reqs.intersection(CRITICAL_REQUIREMENTS)
    critical_coverage=len(critical_observed)/len(CRITICAL_REQUIREMENTS)

    sources=set()
    urls=set()
    fresh_rows=0
    total_rows=0
    artifact_paths=set()

    for task in observed:
        artifacts=task.get("evidence_artifacts")
        if not isinstance(artifacts,list):
            continue
        for item in artifacts:
            path_value=item.get("path") if isinstance(item,dict) else item
            if not path_value:
                continue
            artifact_paths.add(str(path_value))
            for row in _evidence_rows_from_artifact(path_value):
                total_rows+=1
                source=str(
                    row.get("publisher")
                    or row.get("source")
                    or row.get("domain")
                    or ""
                ).strip().lower()
                if source:
                    sources.add(source)

                url=str(row.get("url") or row.get("link") or "").strip()
                if url:
                    urls.add(url)

                observed_at=row.get("observed_at")
                try:
                    ts=float(observed_at)
                except Exception:
                    ts=0.0

                if ts<=0:
                    try:
                        ts=Path(str(path_value)).stat().st_mtime
                    except Exception:
                        ts=0.0

                if ts>0 and now-ts <= 14*86400:
                    fresh_rows+=1

    freshness=(fresh_rows/total_rows) if total_rows else 0.0
    source_diversity=min(1.0,len(sources)/4.0)

    quality=100.0*(
        0.40*coverage
        +0.30*critical_coverage
        +0.15*freshness
        +0.15*source_diversity
    )

    missing=[
        req for req in CORE_REQUIREMENTS
        if req not in observed_reqs
    ]

    return {
        "candidate":name,
        "task_count":len(tasks),
        "observed_task_count":len(observed),
        "observed_requirements":sorted(observed_reqs),
        "missing_requirements":missing,
        "coverage":round(coverage,4),
        "critical_coverage":round(critical_coverage,4),
        "unique_source_count":len(sources),
        "unique_url_count":len(urls),
        "artifact_count":len(artifact_paths),
        "evidence_row_count":total_rows,
        "freshness_score":round(freshness*100.0,2),
        "source_diversity_score":round(source_diversity*100.0,2),
        "evidence_quality_score":round(clamp(quality),2),
    }


def apply_metrics(path:Path,payload:dict[str,Any],metrics:dict[str,Any])->dict[str,Any]:
    before={
        "expected_profit":payload.get("expected_profit"),
        "expected_profit_dollars":payload.get("expected_profit_dollars"),
        "probability":payload.get("probability"),
        "probability_of_success":payload.get("probability_of_success"),
    }

    payload["observed_evidence_count"]=metrics["observed_task_count"]
    payload["observed_evidence_requirements"]=metrics["observed_requirements"]
    payload["observed_evidence_coverage"]=metrics["coverage"]
    payload["critical_evidence_coverage"]=metrics["critical_coverage"]
    payload["missing_evidence_requirements"]=metrics["missing_requirements"]
    payload["evidence_count"]=max(
        int(payload.get("evidence_count") or 0),
        int(metrics["evidence_row_count"]),
        int(metrics["artifact_count"]),
    )
    payload["evidence_quality"]=metrics["evidence_quality_score"]
    payload["evidence_confidence"]=metrics["evidence_quality_score"]
    payload["evidence_source_diversity"]=metrics["source_diversity_score"]
    payload["evidence_freshness_score"]=metrics["freshness_score"]
    payload["evidence_rescored_at_unix"]=time.time()
    payload["evidence_rescoring_policy"]="verified_evidence_only_no_economic_fabrication"

    atomic(path,payload)

    after={
        "expected_profit":payload.get("expected_profit"),
        "expected_profit_dollars":payload.get("expected_profit_dollars"),
        "probability":payload.get("probability"),
        "probability_of_success":payload.get("probability_of_success"),
    }

    return {
        "economics_unchanged":before==after,
        "economics_before":before,
        "economics_after":after,
    }


def _engine_scores()->dict[str,float]:
    from companyos.runtime import profit_opportunity_engine as poe

    scores={}
    for row in poe.discover():
        name=str(row.name or "").strip().lower()
        if not name:
            continue
        current=scores.get(name)
        if current is None or float(row.score)>current:
            scores[name]=float(row.score)
    return scores


def cycle(max_candidates:int=50)->dict[str,Any]:
    queue=load(QUEUE,{"tasks":[]})
    if not isinstance(queue,dict):
        queue={"tasks":[]}

    pre_scores=_engine_scores()

    updates=[]
    changed=0
    for path,payload in candidate_files()[:max(1,int(max_candidates))]:
        name=candidate_name(payload,path)
        metrics=evidence_metrics(name,queue)
        previous_quality=clamp(
            payload.get("evidence_quality")
            or payload.get("evidence_confidence")
            or 0
        )
        previous_coverage=float(payload.get("observed_evidence_coverage") or 0)

        invariant=apply_metrics(path,payload,metrics)

        if (
            abs(previous_quality-metrics["evidence_quality_score"])>0.001
            or abs(previous_coverage-metrics["coverage"])>0.0001
        ):
            changed+=1

        updates.append({
            **metrics,
            "path":str(path),
            "previous_evidence_quality":round(previous_quality,2),
            "evidence_quality_delta":round(
                metrics["evidence_quality_score"]-previous_quality,
                2,
            ),
            "previous_coverage":round(previous_coverage,4),
            "coverage_delta":round(
                metrics["coverage"]-previous_coverage,
                4,
            ),
            **invariant,
        })

    try:
        from companyos.runtime.candidate_enrichment_bridge import refresh_enrichments
        enrichment=refresh_enrichments(max_age_hours=168)
    except Exception as exc:
        enrichment={
            "healthy":False,
            "error":f"{type(exc).__name__}:{str(exc)[:800]}",
        }

    post_scores=_engine_scores()

    movements=[]
    for item in updates:
        key=item["candidate"].strip().lower()
        before=pre_scores.get(key)
        after=post_scores.get(key)
        movements.append({
            "candidate":item["candidate"],
            "score_before":before,
            "score_after":after,
            "score_delta":(
                round(after-before,2)
                if before is not None and after is not None
                else None
            ),
            "evidence_quality":item["evidence_quality_score"],
            "coverage":item["coverage"],
            "critical_coverage":item["critical_coverage"],
            "missing_requirements":item["missing_requirements"],
        })

    movements.sort(
        key=lambda x:(
            -(x["score_after"] if x["score_after"] is not None else -1),
            x["candidate"].lower(),
        )
    )

    state={
        "schema":"companyos.evidence_coverage_rescoring.v69_33",
        "running":True,
        "healthy":True,
        "last_cycle_unix":time.time(),
        "candidate_count":len(updates),
        "candidates_changed":changed,
        "full_coverage_count":sum(
            1 for x in updates if x["coverage"]>=1.0
        ),
        "critical_coverage_complete_count":sum(
            1 for x in updates if x["critical_coverage"]>=1.0
        ),
        "average_coverage":round(
            sum(x["coverage"] for x in updates)/len(updates),
            4,
        ) if updates else 0.0,
        "average_evidence_quality":round(
            sum(x["evidence_quality_score"] for x in updates)/len(updates),
            2,
        ) if updates else 0.0,
        "candidate_updates":updates,
        "ranking_movements":movements[:30],
        "candidate_enrichment":enrichment,
        "economic_values_auto_modified":False,
        "external_messages_sent":False,
        "financial_actions_performed":False,
        "deployments_performed":False,
        "account_creation_performed":False,
        "public_key_harvesting_performed":False,
    }
    atomic(STATE,state)
    append_history({
        "ts":state["last_cycle_unix"],
        "candidate_count":state["candidate_count"],
        "candidates_changed":state["candidates_changed"],
        "average_coverage":state["average_coverage"],
        "average_evidence_quality":state["average_evidence_quality"],
        "ranking_movements":state["ranking_movements"][:10],
    })
    return state


if __name__=="__main__":
    import argparse

    parser=argparse.ArgumentParser()
    parser.add_argument(
        "command",
        nargs="?",
        default="once",
        choices=("once","status"),
    )
    parser.add_argument("--max-candidates",type=int,default=50)
    args=parser.parse_args()

    if args.command=="once":
        print(json.dumps(
            cycle(max_candidates=args.max_candidates),
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
