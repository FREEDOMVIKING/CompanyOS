#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path.home() / "companyos"
RT = ROOT / ".companyos_runtime"
PLANS = RT / "execution_plans"
AGENT_RUNS = RT / "agent_runs"
DIRECTIVES = RT / "venture_directives"
STATE = RT / "venture_execution_director_state.json"
LEDGER = RT / "venture_execution_director_ledger.jsonl"

DIRECTIVES.mkdir(parents=True, exist_ok=True)

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
    event = dict(event)
    event.setdefault("ts", time.time())
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")

def collect_agent_outputs(venture_id):
    items = []
    for p in sorted(AGENT_RUNS.glob(f"{venture_id}-*.json")):
        d = load(p, {})
        if isinstance(d, dict):
            items.append(d)
    return items

def build_milestones(plan, agent_outputs):
    vid = plan.get("venture_id")
    roles = {x.get("role") for x in agent_outputs if isinstance(x,dict)}

    milestones = [
        {
            "milestone_id": f"{vid}-m1-evidence",
            "title": "Resolve critical evidence gaps",
            "status": "ready",
            "type": "internal",
            "required_roles": ["market_research_agent","risk_governance_agent"],
            "success_criteria": [
                "critical evidence gaps documented",
                "launch blockers identified",
                "assumptions explicitly labeled",
            ],
            "external_action": False,
            "financial_action": False,
        },
        {
            "milestone_id": f"{vid}-m2-offer",
            "title": "Finalize offer and business model",
            "status": "ready",
            "type": "internal",
            "required_roles": ["product_strategy_agent","growth_strategy_agent"],
            "success_criteria": [
                "target customer defined",
                "minimum viable offer defined",
                "pricing hypothesis documented",
                "positioning documented",
            ],
            "external_action": False,
            "financial_action": False,
        },
        {
            "milestone_id": f"{vid}-m3-build",
            "title": "Create internal build specification",
            "status": "ready",
            "type": "internal",
            "required_roles": ["technical_architect_agent"],
            "success_criteria": [
                "architecture outline complete",
                "dependencies listed",
                "test criteria defined",
            ],
            "external_action": False,
            "financial_action": False,
        },
        {
            "milestone_id": f"{vid}-m4-launch-review",
            "title": "Launch readiness review",
            "status": "blocked_until_internal_complete",
            "type": "gate",
            "required_roles": ["risk_governance_agent"],
            "success_criteria": [
                "internal milestones complete",
                "risk review complete",
                "external and financial gates evaluated",
            ],
            "external_action": False,
            "financial_action": False,
        },
    ]

    missing = []
    for role in ["market_research_agent","product_strategy_agent","technical_architect_agent","growth_strategy_agent","risk_governance_agent"]:
        if role not in roles:
            missing.append(role)

    return milestones, missing

def process():
    processed = []
    for p in sorted(PLANS.glob("*.json")):
        plan = load(p, {})
        if not isinstance(plan, dict):
            continue
        if plan.get("status") not in ("internal_work_complete","blocked_pending_policy","in_progress","planned"):
            continue

        vid = plan.get("venture_id")
        if not vid:
            continue

        outputs = collect_agent_outputs(vid)
        milestones, missing_roles = build_milestones(plan, outputs)

        directive = {
            "venture_id": vid,
            "plan_id": plan.get("plan_id"),
            "generated_at": time.time(),
            "agent_outputs_found": len(outputs),
            "missing_specialist_roles": missing_roles,
            "priority_score": plan.get("opportunity_score"),
            "execution_status": "ready_for_internal_execution" if not missing_roles else "waiting_on_specialists",
            "milestones": milestones,
            "launch_policy": {
                "internal_work_may_run_autonomously": True,
                "external_actions_require_existing_gate": True,
                "financial_actions_require_existing_gate": True,
                "irreversible_actions_default_blocked": True,
            },
        }

        save(DIRECTIVES / f"{vid}.json", directive)
        processed.append({
            "venture_id": vid,
            "directive": str(DIRECTIVES / f"{vid}.json"),
            "execution_status": directive["execution_status"],
            "milestones": len(milestones),
        })
        ledger({
            "event":"venture_directive_created",
            "venture_id":vid,
            "execution_status":directive["execution_status"],
            "milestone_count":len(milestones),
        })

    out = {
        "ok": True,
        "processed_at": time.time(),
        "directives_created": len(processed),
        "results": processed,
    }
    save(STATE, out)
    return out

action = __import__("sys").argv[1] if len(__import__("sys").argv)>1 else "status"
if action == "process":
    emit(process())
elif action == "status":
    emit(load(STATE, {"ok":True,"status":"not_run"}))
else:
    emit({"ok":False,"reason":"unsupported_action","action":action},2)
