from __future__ import annotations
import hashlib, json, time
from pathlib import Path
from typing import Any
from companyos.runtime.autonomous_task_dispatcher import AutonomousTaskDispatcher

RUNTIME=Path.home()/".companyos_runtime"
EVIDENCE=RUNTIME/"specialist_evidence"
EVIDENCE.mkdir(parents=True,exist_ok=True)

def _payload(task)->dict[str,Any]:
    return task.payload if isinstance(task.payload,dict) else {}

def _text(p,*keys):
    for k in keys:
        v=p.get(k)
        if isinstance(v,str) and v.strip(): return v.strip()
    return ""

def _write(task,kind,body):
    safe="".join(c for c in str(task.task_id) if c.isalnum() or c in "-_")[:120]
    path=EVIDENCE/f"{safe}.{kind}.json"
    rec={"schema":"companyos.specialist_evidence.v1","task_id":task.task_id,
         "task_type":task.task_type,"created_at_unix":time.time(),**body}
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(rec,indent=2,sort_keys=True,default=str)+"\n")
    tmp.replace(path)
    return str(path)

def _require(ok,reason):
    if not ok: raise RuntimeError(reason)

def register_default_specialists(dispatcher:AutonomousTaskDispatcher)->None:
    # V31: evidence-backed internal specialists. No fabricated external work.
    def research(task):
        p=_payload(task)
        subject=_text(p,"topic","goal","directive","objective","query","name")
        _require(bool(subject),"research_missing_subject")
        supplied=p.get("evidence") or p.get("sources") or p.get("observations") or []
        if not isinstance(supplied,(list,dict)): supplied=[str(supplied)]
        try:
            from companyos.runtime.research_candidate_synthesizer import run_for_task
            synthesis=run_for_task(subject,supplied)
        except Exception as exc:
            synthesis={
                "candidate_count":0,
                "candidate_files":[],
                "external_research_performed":False,
                "synthesis_mode":"error",
                "error":f"{type(exc).__name__}:{exc}",
                "execution_ready_candidates_created":0,
            }
        artifact=_write(task,"research",{
            "subject":subject,
            "payload_sha256":hashlib.sha256(json.dumps(p,sort_keys=True,default=str).encode()).hexdigest(),
            "supplied_evidence":supplied,
            "external_research_performed":bool(synthesis.get("external_research_performed")),
            "candidate_synthesis":synthesis,
            "candidate_count":int(synthesis.get("candidate_count",0) or 0),
            "candidate_files":synthesis.get("candidate_files",[]),
            "status":"grounded_research_candidate_synthesis_attempted",
            "next_requirement":"enrich low-confidence hypotheses before guarded execution"})
        return {"agent":"research_agent","status":"research_candidate_synthesis_attempted",
                "artifact":artifact,
                "candidate_count":int(synthesis.get("candidate_count",0) or 0),
                "candidate_files":synthesis.get("candidate_files",[]),
                "synthesis_mode":synthesis.get("synthesis_mode"),
                "external_research_performed":bool(synthesis.get("external_research_performed")),
                "external_claims_invented":False,
                "execution_ready_candidates_created":0}

    def planning(task):
        p=_payload(task)
        goal=_text(p,"goal","directive","objective","topic","name")
        _require(bool(goal),"planning_missing_goal")
        constraints=p.get("constraints",[])
        if not isinstance(constraints,list): constraints=[str(constraints)]
        steps=[
          {"stage":"validate_inputs","done_when":"required evidence is present"},
          {"stage":"select_execution_path","done_when":"dependencies and gates are resolved"},
          {"stage":"execute","done_when":"observable artifact or action result exists"},
          {"stage":"verify_outcome","done_when":"result evidence passes validation"}]
        artifact=_write(task,"plan",{"goal":goal,"constraints":constraints,
                                     "steps":steps,"status":"internal_plan_materialized"})
        return {"agent":"planning_agent","status":"plan_artifact_created",
                "artifact":artifact,"step_count":len(steps)}

    def build(task):
        p=_payload(task)
        name=_text(p,"name","goal","directive","objective","topic")
        _require(bool(name),"build_missing_target")
        artifact=_write(task,"build",{
            "target":name,"requested_artifact":p.get("artifact") or p.get("deliverable"),
            "inputs":p,"status":"build_manifest_materialized",
            "external_deployment_performed":False})
        _require(Path(artifact).exists() and Path(artifact).stat().st_size>0,
                 "build_artifact_not_persisted")
        return {"agent":"builder_agent","status":"build_artifact_created",
                "artifact":artifact,"external_deployment_performed":False}

    dispatcher.register(task_type="research",agent_name="research_agent",handler=research)
    dispatcher.register(task_type="planning",agent_name="planning_agent",handler=planning)
    dispatcher.register(task_type="build",agent_name="builder_agent",handler=build)
