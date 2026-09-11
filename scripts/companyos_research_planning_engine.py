#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path.home() / "companyos"
RT = ROOT / ".companyos_runtime"
OPP = RT / "opportunities" / "scored_opportunities.json"
RESEARCH = RT / "research"
PLANS = RT / "execution_plans"
STATE = RT / "research_planning_state.json"
LEDGER = RT / "research_planning_ledger.jsonl"

for p in (RESEARCH, PLANS):
    p.mkdir(parents=True, exist_ok=True)

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

def plan_id(venture_id):
    return hashlib.sha256(f"{venture_id}|plan".encode()).hexdigest()[:16]

def research_for(op):
    vid = str(op.get("opportunity_id") or op.get("venture_id") or "").strip()
    if not vid:
        return None

    # Evidence-aware synthesis only from known structured fields.
    known = {
        "venture_id": vid,
        "title": op.get("title") or op.get("name"),
        "market": op.get("market"),
        "business_model": op.get("model"),
        "score": op.get("score"),
        "evidence_quality": op.get("evidence_quality"),
        "demand_evidence": op.get("demand_evidence"),
        "margin_potential": op.get("margin_potential"),
        "speed_to_revenue": op.get("speed_to_revenue"),
        "capability_fit": op.get("capability_fit"),
        "execution_risk": op.get("execution_risk"),
        "capital_intensity": op.get("capital_intensity"),
        "source": op.get("source"),
        "generated_at": time.time(),
    }

    gaps = []
    for field in ("market", "business_model", "demand_evidence", "evidence_quality"):
        if known.get(field) in (None, "", 0):
            gaps.append(field)

    report = {
        "venture_id": vid,
        "research_status": "sufficient_for_planning" if not gaps else "planning_with_gaps",
        "known_evidence": known,
        "evidence_gaps": gaps,
        "assumptions_allowed": False,
        "external_research_required": bool(gaps),
    }

    save(RESEARCH / f"{vid}.json", report)
    ledger({"event":"research_report_created","venture_id":vid,"gaps":gaps})
    return report

def build_plan(op, research):
    vid = str(op.get("opportunity_id") or op.get("venture_id") or "").strip()
    title = op.get("title") or op.get("name") or vid

    tasks = [
        {
            "task_id": f"{vid}-research-validate",
            "role": "market_research_agent",
            "objective": "Validate market demand, customer pain, competitors, and pricing using available evidence.",
            "requires_external_action": False,
            "requires_financial_action": False,
            "status": "queued",
        },
        {
            "task_id": f"{vid}-offer-design",
            "role": "product_strategy_agent",
            "objective": "Design the smallest credible offer, target customer, pricing hypothesis, and differentiation.",
            "requires_external_action": False,
            "requires_financial_action": False,
            "status": "queued",
        },
        {
            "task_id": f"{vid}-build-plan",
            "role": "technical_architect_agent",
            "objective": "Produce build architecture, dependencies, delivery milestones, and test criteria.",
            "requires_external_action": False,
            "requires_financial_action": False,
            "status": "queued",
        },
        {
            "task_id": f"{vid}-go-to-market",
            "role": "growth_strategy_agent",
            "objective": "Create launch channels, acquisition experiments, messaging, and success metrics.",
            "requires_external_action": False,
            "requires_financial_action": False,
            "status": "queued",
        },
        {
            "task_id": f"{vid}-risk-review",
            "role": "risk_governance_agent",
            "objective": "Review legal, financial, execution, safety, and irreversible-action risks before launch.",
            "requires_external_action": False,
            "requires_financial_action": False,
            "status": "queued",
        },
    ]

    plan = {
        "plan_id": plan_id(vid),
        "venture_id": vid,
        "title": title,
        "created_at": time.time(),
        "opportunity_score": op.get("score"),
        "research_status": research.get("research_status"),
        "evidence_gaps": research.get("evidence_gaps"),
        "tasks": tasks,
        "launch_gate": {
            "external_actions_require_existing_policy_approval": True,
            "financial_actions_require_existing_limits_and_approval": True,
            "irreversible_actions_default_blocked": True,
        },
        "status": "planned",
    }

    save(PLANS / f"{vid}.json", plan)
    ledger({"event":"execution_plan_created","venture_id":vid,"task_count":len(tasks)})
    return plan

def process_top(limit=3):
    ops = load(OPP, [])
    if not isinstance(ops, list):
        ops = []

    qualified = [x for x in ops if isinstance(x, dict) and x.get("qualified")]
    results = []

    for op in qualified[:max(1,limit)]:
        research = research_for(op)
        if not research:
            continue
        plan = build_plan(op, research)
        results.append({
            "venture_id": plan["venture_id"],
            "research_status": research["research_status"],
            "plan_id": plan["plan_id"],
            "task_count": len(plan["tasks"]),
        })

    state = {
        "ok": True,
        "processed_at": time.time(),
        "qualified_seen": len(qualified),
        "planned": len(results),
        "results": results,
    }
    save(STATE, state)
    return state

def status():
    return load(STATE, {"ok":True,"status":"not_run"})

action = sys.argv[1] if len(sys.argv)>1 else "status"
if action == "process":
    out = process_top(int(os.getenv("COMPANYOS_RESEARCH_PLAN_TOP_N","3")))
elif action == "status":
    out = status()
else:
    emit({"ok":False,"reason":"unsupported_action","action":action},2)

emit(out)
