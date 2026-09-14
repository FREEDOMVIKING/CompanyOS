from __future__ import annotations
import json, time
from pathlib import Path

ROOT = Path.home() / "companyos"
RUNTIME_FILES = [
    ROOT / "companyos_runtime" / "autonomous_ceo_runtime_service.json",
    ROOT / ".companyos_runtime" / "autonomous_ceo_runtime_service.json",
]
STATE = ROOT / ".companyos_runtime" / "idle_cycle_recovery_state.json"

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

def empty_cycle_detected(min_idle_cycles=25):
    rt = runtime_state()
    active = int(rt.get("active_orchestrations", 0) or 0)
    dispatched = int(rt.get("cycles_dispatched_this_tick", 0) or 0)
    cycle_count = int(rt.get("cycle_count", 0) or 0)
    last_oid = rt.get("last_orchestration_id")

    st = load(STATE, {
        "last_cycle_count": cycle_count,
        "last_productive_cycle_count": cycle_count,
        "recoveries": [],
    })

    if active > 0 or dispatched > 0 or last_oid:
        st["last_productive_cycle_count"] = cycle_count
        st["last_cycle_count"] = cycle_count
        save(STATE, st)
        return False, {"reason": "productive_runtime", "runtime": rt}

    last_productive = int(st.get("last_productive_cycle_count", cycle_count) or cycle_count)
    idle_cycles = max(0, cycle_count - last_productive)
    st["last_cycle_count"] = cycle_count
    save(STATE, st)

    return idle_cycles >= min_idle_cycles, {
        "reason": "empty_cycle_threshold" if idle_cycles >= min_idle_cycles else "below_threshold",
        "idle_cycles": idle_cycles,
        "runtime": rt,
    }

def recovery_goal():
    try:
        from companyos.strategy.diversified_opportunity_governor import discovery_directive
        base = discovery_directive()
    except Exception:
        base = (
            "Run a diversified CompanyOS opportunity discovery cycle. "
            "Discover at least 12 genuinely different opportunities across at least 6 unrelated sectors. "
            "Score them by demand, margin, automation potential, scalability, time-to-revenue, feasibility, "
            "competition, and startup cost. Recommend no more than 3 for active validation."
        )

    return base + (
        "\n\nIDLE-CYCLE RECOVERY REQUIREMENTS:\n"
        "- Recover from repeated empty CEO cycles with zero active orchestrations and zero dispatched work.\n"
        "- Do not merely return a recommendation or status report.\n"
        "- Create and dispatch concrete INTERNAL and REVERSIBLE research/planning/validation tasks.\n"
        "- Produce at least one persisted state change: task queue entry, research artifact, ranked opportunity file, "
        "validation plan, or orchestration record.\n"
        "- Reuse existing CompanyOS agents and task queues.\n"
        "- Do not clone the Local Contractor Bid Organizer or create version-suffixed duplicates.\n"
        "- Keep consequential external actions, financial transactions, spending, credential changes, destructive "
        "actions, and irreversible commitments behind existing approval and safety gates."
    )

def start_recovery():
    from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator

    rec = AutonomousCEOOrchestrator().start(
        goal=recovery_goal(),
        max_cycles=100,
        max_follow_up_depth=4,
        priority_base=220,
    )
    oid = getattr(rec, "orchestration_id", None)

    st = load(STATE, {"recoveries": []})
    entry = {"ts": time.time(), "orchestration_id": oid, "action": "idle_cycle_recovery_started"}
    st.setdefault("recoveries", []).append(entry)
    st["recoveries"] = st["recoveries"][-100:]
    st["last_recovery_unix"] = entry["ts"]
    st["last_productive_cycle_count"] = int(runtime_state().get("cycle_count", 0) or 0)
    save(STATE, st)
    return entry

def maybe_recover(min_idle_cycles=25, cooldown_seconds=300):
    stalled, detail = empty_cycle_detected(min_idle_cycles=min_idle_cycles)
    if not stalled:
        return {"started": False, **detail}

    st = load(STATE, {})
    last = float(st.get("last_recovery_unix", 0) or 0)
    if time.time() - last < cooldown_seconds:
        return {"started": False, "reason": "cooldown", **detail}

    try:
        return {"started": True, "entry": start_recovery(), **detail}
    except Exception as exc:
        return {
            "started": False,
            "reason": "recovery_start_failed",
            "error": f"{type(exc).__name__}: {exc}",
            **detail,
        }
