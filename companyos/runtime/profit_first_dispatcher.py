from __future__ import annotations
import json, time
from pathlib import Path

ROOT = Path.home() / "companyos"
STATE = ROOT / ".companyos_runtime" / "profit_first_dispatcher_state.json"
RUNTIME_FILES = [
    ROOT / "companyos_runtime" / "autonomous_ceo_runtime_service.json",
    ROOT / ".companyos_runtime" / "autonomous_ceo_runtime_service.json",
]

def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

def runtime_state():
    merged = {}
    for p in RUNTIME_FILES:
        if p.exists():
            obj = load(p, {})
            if isinstance(obj, dict):
                merged.update(obj)
    return merged

def dispatcher_state():
    return load(STATE, {
        "last_dispatch_unix": 0,
        "dispatches": [],
        "last_seen_cycle": 0,
        "last_productive_cycle": 0,
    })

def should_dispatch(min_idle_cycles=20, cooldown_seconds=300):
    rt = runtime_state()
    st = dispatcher_state()
    cycle = int(rt.get("cycle_count", 0) or 0)
    idle = (
        bool(rt.get("ready", True))
        and int(rt.get("active_orchestrations", 0) or 0) == 0
        and int(rt.get("cycles_dispatched_this_tick", 0) or 0) == 0
        and not rt.get("last_orchestration_id")
    )

    if not idle:
        st["last_productive_cycle"] = cycle
        st["last_seen_cycle"] = cycle
        save(STATE, st)
        return False, {"reason": "runtime_not_idle", "runtime": rt}

    if not st.get("last_seen_cycle"):
        st["last_seen_cycle"] = cycle
        st["last_productive_cycle"] = max(0, cycle - min_idle_cycles)

    idle_cycles = max(0, cycle - int(st.get("last_productive_cycle", cycle) or cycle))
    since_last = time.time() - float(st.get("last_dispatch_unix", 0) or 0)
    st["last_seen_cycle"] = cycle
    save(STATE, st)

    if idle_cycles < min_idle_cycles:
        return False, {"reason": "below_idle_threshold", "idle_cycles": idle_cycles, "runtime": rt}
    if since_last < cooldown_seconds:
        return False, {"reason": "dispatch_cooldown", "idle_cycles": idle_cycles, "runtime": rt}
    return True, {"reason": "profit_first_dispatch_ready", "idle_cycles": idle_cycles, "runtime": rt}

def build_goal():
    from companyos.strategy.profit_first_venture_engine import discovery_directive
    return discovery_directive() + """
AUTONOMOUS DISPATCH REQUIREMENTS:
- This is a live CEO dispatch, not a status-only analysis.
- Create concrete INTERNAL, REVERSIBLE work that advances opportunity discovery and validation.
- Persist a ranked candidate set or equivalent evidence artifact.
- If strong candidates exist, create concrete validation tasks for at most the top 3.
- If no candidate clears the investment threshold, persist findings and continue research instead of forcing a build.
- Compare against existing ventures before opening a new validation bet.
- Prefer improving or scaling an existing demonstrated winner when its expected value is higher.
- Do not count renamed/versioned copies of existing ventures as new opportunities.
- Preserve all existing approval, spending, financial transaction, credential, signer, reconciliation,
  publication/deployment, destructive-action, legal-commitment, and irreversible-action gates.
"""

def dispatch_profit_first():
    from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
    rec = AutonomousCEOOrchestrator().start(
        goal=build_goal(),
        max_cycles=120,
        max_follow_up_depth=4,
        priority_base=240,
    )
    oid = getattr(rec, "orchestration_id", None)
    now = time.time()
    st = dispatcher_state()
    st["last_dispatch_unix"] = now
    st["last_productive_cycle"] = int(runtime_state().get("cycle_count", 0) or 0)
    entry = {"ts": now, "action": "profit_first_dispatch_started", "orchestration_id": oid}
    st.setdefault("dispatches", []).append(entry)
    st["dispatches"] = st["dispatches"][-100:]
    save(STATE, st)
    return {"started": True, "orchestration_id": oid, "entry": entry}

def maybe_dispatch(min_idle_cycles=20, cooldown_seconds=300):
    ok, detail = should_dispatch(min_idle_cycles, cooldown_seconds)
    if not ok:
        return {"started": False, **detail}
    try:
        return {**dispatch_profit_first(), **detail}
    except Exception as exc:
        return {
            "started": False,
            "reason": "profit_first_dispatch_failed",
            "error": f"{type(exc).__name__}: {exc}",
            **detail,
        }


# COMPANYOS_TARGETED_ENRICHMENT_CONTRACT_V3
_profit_first_build_goal_v3_base = build_goal
def build_goal():
    q = load(ROOT / ".companyos_runtime" / "profit_candidate_enrichment_queue.json", {})
    rows = q.get("candidates", []) if isinstance(q, dict) else []
    focus = []
    for row in rows[:8]:
        if isinstance(row, dict):
            focus.append({"name":row.get("name"),"missing_or_blocking":row.get("missing_or_blocking"),"current":row.get("current")})
    return _profit_first_build_goal_v3_base() + """
TARGETED ENRICHMENT CONTRACT:
- Prioritize the current enrichment queue instead of broad generic research.
- Resolve specific gaps with real evidence.
- A usable candidate needs a buyer, problem, offer/revenue mechanism, at least one evidence source, and one executable next action.
- Estimate profit, probability, readiness, time-to-cash, and capital only when evidence supports it.
- Never invent evidence, customers, revenue, or probability.
- Save structured commercial research into canonical_research_outputs for ingestion.
- Avoid duplicate or renamed opportunities.
- Preserve all connector, approval, finance, credential, signer, deployment, legal, destructive-action, and irreversible-action gates.
CURRENT ENRICHMENT QUEUE:
""" + json.dumps(focus, indent=2, default=str)



# COMPANYOS_CAPABILITY_GUIDED_EXECUTION_V17
_profit_first_build_goal_v17_base = build_goal
def build_goal():
    base = _profit_first_build_goal_v17_base()
    q = load(ROOT / ".companyos_runtime" / "profit_execution_action_queue.json", {})
    rows = q.get("actions", []) if isinstance(q, dict) else []
    packet = rows[-1] if rows and isinstance(rows[-1], dict) else None
    if not packet:
        return base

    safe_packet = {
        "action_packet_id": packet.get("action_packet_id"),
        "candidate_name": packet.get("candidate_name"),
        "candidate_score": packet.get("candidate_score"),
        "recommended_actions": packet.get("recommended_actions"),
        "required_execution_contract": packet.get("required_execution_contract"),
    }
    header = "\nCAPABILITY-GUIDED EXECUTION PACKET:\n"
    rules = (
        "- Use the capability-derived actions below to advance the selected opportunity.\n"
        "- Re-evaluate the candidate after each measurable action.\n"
        "- Prefer the highest-confidence reversible action first.\n"
        "- Preserve every existing connector, approval, finance, signer, credential, deployment, legal, destructive-action, and irreversible-action gate.\n"
        "- If an action is blocked by policy or missing evidence, record the blocker and choose the next permitted reversible validation action instead of bypassing the gate.\n"
        "\nCURRENT ACTION PACKET:\n"
    )
    return base + header + rules + json.dumps(safe_packet, indent=2, default=str)


# COMPANYOS_EVIDENCE_ACQUISITION_V19
_profit_first_build_goal_v19_base = build_goal
def build_goal():
    base = _profit_first_build_goal_v19_base()
    evidence_q = load(ROOT / ".companyos_runtime" / "evidence_acquisition_queue.json", {})
    tasks = evidence_q.get("tasks", []) if isinstance(evidence_q, dict) else []
    pending = [
        {
            "task_id": t.get("task_id"),
            "candidate_name": t.get("candidate_name"),
            "requirement": t.get("requirement"),
            "guidance": t.get("guidance"),
            "research_contract": t.get("research_contract"),
        }
        for t in tasks
        if isinstance(t, dict) and t.get("status") == "research_required"
    ][:8]
    if not pending:
        return base
    return base + "\nAUTONOMOUS EVIDENCE ACQUISITION TASKS:\n" + (
        "- Resolve these research-only evidence gaps before treating the candidate as execution-ready.\n"
        "- Use real attributable evidence only. Never fabricate sources or observations.\n"
        "- Write collected research into the normal CompanyOS canonical research-output path so it can be re-evaluated.\n"
        "- Do not send outreach, buy anything, deploy, sign, or transact merely to satisfy an evidence task.\n"
        "- Existing approval, external-action, credential, deployment, and financial gates remain authoritative.\n\n"
        "PENDING EVIDENCE TASKS:\n"
    ) + json.dumps(pending, indent=2, default=str)


# COMPANYOS_EVIDENCE_DECISION_CLOSURE_V20
_profit_first_build_goal_v20_base = build_goal
def build_goal():
    base = _profit_first_build_goal_v20_base()
    q = load(ROOT / ".companyos_runtime" / "profit_execution_action_queue.json", {})
    rows = q.get("actions", []) if isinstance(q, dict) else []
    packet = rows[-1] if rows and isinstance(rows[-1], dict) else None
    if not packet:
        return base

    closure = packet.get("decision_closure")
    if not isinstance(closure, dict):
        return base

    decision = closure.get("decision")
    if decision == "promote_to_guarded_execution":
        return base + "\nEVIDENCE-TO-DECISION CLOSURE:\nCandidate evidence and economics passed the current guarded-readiness rules. Continue through the existing execution gates; do not bypass any connector, approval, finance, credential, deployment, legal, or irreversible-action control.\n"
    if decision == "deprioritize":
        return base + "\nEVIDENCE-TO-DECISION CLOSURE:\nThis candidate is currently deprioritized. Do not spend external resources on it. Record the reason and select the next eligible opportunity.\n"
    return base + "\nEVIDENCE-TO-DECISION CLOSURE:\nCandidate is not yet execution-ready. Continue only the permitted research/validation work needed to close the listed evidence or economic gaps.\n"
