#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path.home() / "companyos"
RT = ROOT / ".companyos_runtime"
PLANS = RT / "execution_plans"
RUNS = RT / "agent_runs"
STATE = RT / "agent_orchestrator_state.json"
LEDGER = RT / "agent_orchestrator_ledger.jsonl"

RUNS.mkdir(parents=True, exist_ok=True)

def emit(obj, code=0):
    print(json.dumps(obj, sort_keys=True))
    raise SystemExit(code)

def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)

def ledger(event):
    event=dict(event)
    event.setdefault("ts",time.time())
    with LEDGER.open("a",encoding="utf-8") as f:
        f.write(json.dumps(event,sort_keys=True)+"\n")

ROLE_OUTPUTS = {
    "market_research_agent": [
        "customer_problem_hypothesis",
        "competitor_map",
        "pricing_evidence_needed",
        "market_validation_questions",
    ],
    "product_strategy_agent": [
        "target_customer",
        "minimum_viable_offer",
        "pricing_hypothesis",
        "differentiation",
    ],
    "technical_architect_agent": [
        "architecture_outline",
        "dependencies",
        "milestones",
        "test_criteria",
    ],
    "growth_strategy_agent": [
        "positioning",
        "launch_channels",
        "acquisition_experiments",
        "success_metrics",
    ],
    "risk_governance_agent": [
        "risk_register",
        "external_action_gates",
        "financial_action_gates",
        "launch_blockers",
    ],
}

def execute_task(plan, task):
    role = task.get("role")
    vid = plan.get("venture_id")
    tid = task.get("task_id")

    # This orchestrator creates structured delegated work products without
    # performing irreversible external or financial actions.
    if task.get("requires_external_action") or task.get("requires_financial_action"):
        return {
            "task_id": tid,
            "role": role,
            "status": "blocked_pending_policy",
            "reason": "external_or_financial_action_requires_existing_policy_gate",
        }

    deliverables = {}
    for key in ROLE_OUTPUTS.get(role, ["analysis"]):
        deliverables[key] = {
            "status": "drafted",
            "note": f"Prepared by {role} for {vid}; requires evidence-backed refinement before external execution."
        }

    result = {
        "task_id": tid,
        "role": role,
        "status": "completed_internal",
        "completed_at": time.time(),
        "deliverables": deliverables,
        "external_actions_performed": False,
        "financial_actions_performed": False,
    }

    save(RUNS / f"{tid}.json", result)
    ledger({"event":"agent_task_completed","venture_id":vid,"task_id":tid,"role":role})
    return result

def process():
    processed=[]
    for p in sorted(PLANS.glob("*.json")):
        plan=load(p,{})
        if not isinstance(plan,dict):
            continue

        changed=False
        task_results=[]
        for task in plan.get("tasks",[]):
            if not isinstance(task,dict):
                continue
            if task.get("status") not in ("queued","retry"):
                continue

            result=execute_task(plan,task)
            task_results.append(result)

            if result["status"]=="completed_internal":
                task["status"]="completed_internal"
                task["completed_at"]=result["completed_at"]
            else:
                task["status"]=result["status"]

            changed=True

        if changed:
            statuses=[t.get("status") for t in plan.get("tasks",[]) if isinstance(t,dict)]
            if statuses and all(s=="completed_internal" for s in statuses):
                plan["status"]="internal_work_complete"
                plan["ready_for_launch_gate_review"]=True
            elif any(s=="blocked_pending_policy" for s in statuses):
                plan["status"]="blocked_pending_policy"
            else:
                plan["status"]="in_progress"

            plan["updated_at"]=time.time()
            save(p,plan)

        if task_results:
            processed.append({
                "venture_id":plan.get("venture_id"),
                "plan_id":plan.get("plan_id"),
                "results":task_results,
                "plan_status":plan.get("status"),
            })

    out={
        "ok":True,
        "processed_at":time.time(),
        "plans_processed":len(processed),
        "results":processed,
    }
    save(STATE,out)
    return out

action=sys.argv[1] if len(sys.argv)>1 else "status"
if action=="process":
    emit(process())
elif action=="status":
    emit(load(STATE,{"ok":True,"status":"not_run"}))
else:
    emit({"ok":False,"reason":"unsupported_action","action":action},2)
