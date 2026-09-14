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

