from __future__ import annotations
# COMPANYOS_REASONING_RELIABILITY_V1
try:
    from companyos.runtime.reasoning_reliability import install as _install_reasoning_reliability
    _install_reasoning_reliability()
except Exception:
    pass

import json
import os
import time
import traceback
from pathlib import Path
from typing import Any
from companyos.strategy.profit_first_enrichment_expansion import maybe_run as maybe_run_profit_first_enrichment_expansion
from companyos.strategy.candidate_materialization_bridge import maybe_recover_missing_outputs as maybe_recover_profit_first_outputs
from companyos.strategy.candidate_materialization_bridge import materialize as materialize_profit_first_candidates
from companyos.strategy.profit_first_research_pipeline import maybe_run as maybe_run_profit_first_research
from companyos.runtime.profit_first_dispatcher import maybe_dispatch as maybe_dispatch_profit_first
from companyos.runtime.idle_cycle_recovery_controller import maybe_recover as maybe_recover_idle_cycles
from companyos.strategy.diversified_opportunity_governor import discovery_directive, should_force_diversified_discovery
from companyos.runtime.stalled_stage_progression_controller import maybe_start as maybe_start_stalled_stage
from companyos.governance.venture_identity_progression import highest_priority_stalled

ROOT = Path.home() / "companyos"
RUNTIME = ROOT / ".companyos_runtime"
STATE_CANDIDATES = [
    ROOT / ".companyos_runtime" / "autonomous_ceo_runtime_service.json",
    ROOT / "companyos_runtime" / "autonomous_ceo_runtime_service.json",
]
WATCHDOG_STATE = RUNTIME / "productive_autonomy_watchdog_state.json"
LOG = RUNTIME / "productive_autonomy_watchdog.log"

DEFAULT_IDLE_CYCLES = int(os.getenv("COMPANYOS_ANTISTALL_IDLE_CYCLES", "25"))
DEFAULT_MIN_SECONDS = int(os.getenv("COMPANYOS_ANTISTALL_MIN_SECONDS", "120"))
MAX_AUTOSTARTS_PER_HOUR = int(os.getenv("COMPANYOS_ANTISTALL_MAX_STARTS_PER_HOUR", "3"))

GOALS = [
    "Evaluate the highest-priority current CompanyOS business opportunity and advance one concrete reversible internal step toward validation or launch. Prefer producing an artifact, customer-ready asset, implementation, or measurable experiment over additional review.",
    "Inspect current roadmap priorities and pending internal work. Choose the highest-value reversible task that is not blocked by a consequential approval gate, execute or delegate it, validate the result, and create the next follow-up task.",
    "Advance the most promising existing venture by completing the next missing internal milestone in research, product build, validation, launch preparation, customer acquisition preparation, or operational readiness. Avoid repeating analysis already completed.",
    "Find a stalled CompanyOS initiative with sufficient evidence to proceed internally. Convert it into concrete tasks, dispatch the first dependency-ready task, validate completion, and schedule a follow-up goal.",
]

def log(msg: str) -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n"
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line)

def read_json(path: Path) -> dict[str, Any]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}

def write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)

def runtime_state() -> tuple[Path | None, dict[str, Any]]:
    for p in STATE_CANDIDATES:
        if p.exists():
            return p, read_json(p)
    return None, {}

def watchdog_state() -> dict[str, Any]:
    s = read_json(WATCHDOG_STATE)
    s.setdefault("last_cycle_count", 0)
    s.setdefault("last_completed", 0)
    s.setdefault("last_progress_unix", time.time())
    s.setdefault("goal_index", 0)
    s.setdefault("autostarts", [])
    s.setdefault("total_autostarts", 0)
    return s

def can_autostart(ws: dict[str, Any]) -> bool:
    cutoff = time.time() - 3600
    recent = [float(x) for x in ws.get("autostarts", []) if float(x) >= cutoff]
    ws["autostarts"] = recent
    return len(recent) < MAX_AUTOSTARTS_PER_HOUR

def start_internal_goal(goal: str) -> str:
    if should_force_diversified_discovery():
        goal = discovery_directive()

    stalled = highest_priority_stalled()
    if stalled:
        goal = stalled["progression_directive"]

    from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
    ceo = AutonomousCEOOrchestrator()
    rec = ceo.start(
        goal=goal,
        max_cycles=60,
        max_follow_up_depth=3,
        priority_base=170 if stalled else 150,
    )
    oid = getattr(rec, "orchestration_id", None)
    return str(oid or "created")

def tick() -> dict[str, Any]:
    profit_first_enrichment_expansion = maybe_run_profit_first_enrichment_expansion(
        cooldown_seconds=int(os.getenv("COMPANYOS_PROFIT_FIRST_ENRICHMENT_COOLDOWN_SECONDS", "300")),
    )
    if profit_first_enrichment_expansion.get("started"):
        log("PROFIT_FIRST_ENRICHMENT_EXPANSION " + json.dumps(profit_first_enrichment_expansion, default=str, sort_keys=True))

    candidate_materialization = materialize_profit_first_candidates()
    if candidate_materialization.get("candidate_files_written_or_updated", 0) > 0:
        log("PROFIT_FIRST_CANDIDATES_MATERIALIZED " + json.dumps(candidate_materialization, default=str, sort_keys=True))

    candidate_recovery = maybe_recover_profit_first_outputs(
        min_expected_candidates=1,
        cooldown_seconds=int(os.getenv("COMPANYOS_CANDIDATE_RECOVERY_COOLDOWN_SECONDS", "300")),
    )
    if candidate_recovery.get("started"):
        log("PROFIT_FIRST_CANDIDATE_RECOVERY " + json.dumps(candidate_recovery, default=str, sort_keys=True))

    profit_first_research = maybe_run_profit_first_research(
        cooldown_seconds=int(os.getenv("COMPANYOS_PROFIT_FIRST_RESEARCH_COOLDOWN_SECONDS", "300")),
    )
    if profit_first_research.get("started"):
        log("PROFIT_FIRST_RESEARCH " + json.dumps(profit_first_research, default=str, sort_keys=True))

    profit_first_dispatch = maybe_dispatch_profit_first(
        min_idle_cycles=int(os.getenv("COMPANYOS_PROFIT_FIRST_DISPATCH_MIN_IDLE_CYCLES", "20")),
        cooldown_seconds=int(os.getenv("COMPANYOS_PROFIT_FIRST_DISPATCH_COOLDOWN_SECONDS", "300")),
    )
    if profit_first_dispatch.get("started"):
        log("PROFIT_FIRST_DISPATCH " + json.dumps(profit_first_dispatch, default=str, sort_keys=True))

    idle_recovery = maybe_recover_idle_cycles(
        min_idle_cycles=int(os.getenv("COMPANYOS_IDLE_RECOVERY_MIN_CYCLES", "25")),
        cooldown_seconds=int(os.getenv("COMPANYOS_IDLE_RECOVERY_COOLDOWN_SECONDS", "300")),
    )
    if idle_recovery.get("started"):
        log("IDLE_CYCLE_RECOVERY " + json.dumps(idle_recovery, default=str, sort_keys=True))

    p, rs = runtime_state()
    if not rs:
        return {"ok": False, "reason": "runtime_state_missing"}

    ws = watchdog_state()
    now = time.time()

    cycles = int(rs.get("cycle_count", 0) or 0)
    completed = int(rs.get("completed_orchestrations", 0) or 0)
    active = int(rs.get("active_orchestrations", 0) or 0)
    failed = int(rs.get("failed_orchestrations", 0) or 0)
    halted = int(rs.get("halted_orchestrations", 0) or 0)
    running = bool(rs.get("running", False))
    ready = bool(rs.get("ready", False))

    progressed = completed > int(ws.get("last_completed", 0))
    if progressed:
        ws["last_progress_unix"] = now
        ws["last_completed"] = completed

    delta_cycles = cycles - int(ws.get("last_cycle_count", cycles))
    idle_for = now - float(ws.get("last_progress_unix", now))

    should_start = (
        running and ready and active == 0
        and delta_cycles >= DEFAULT_IDLE_CYCLES
        and idle_for >= DEFAULT_MIN_SECONDS
        and can_autostart(ws)
    )

    action = "observe"
    new_orchestration_id = None
    if should_start:
        stalled = maybe_start_stalled_stage(
            min_unchanged=int(os.getenv("COMPANYOS_STALLED_STAGE_MIN_OBSERVATIONS", "3")),
            cooldown_seconds=int(os.getenv("COMPANYOS_STALLED_STAGE_COOLDOWN_SECONDS", "300")),
        )
        if stalled.get("started"):
            entry = stalled.get("entry") or {}
            action = "autostart_stalled_stage_progression"
            new_orchestration_id = entry.get("orchestration_id")
            ws["autostarts"].append(now)
            ws["total_autostarts"] = int(ws.get("total_autostarts", 0)) + 1
            ws["last_progress_unix"] = now
            ws["last_cycle_count"] = cycles
            log("STALLED_STAGE_AUTOSTART " + json.dumps(entry, default=str, sort_keys=True))
            should_start = False

    if should_start:
        idx = int(ws.get("goal_index", 0)) % len(GOALS)
        goal = GOALS[idx]
        try:
            new_orchestration_id = start_internal_goal(goal)
            action = "autostart_internal_goal"
            ws["goal_index"] = idx + 1
            ws["autostarts"].append(now)
            ws["total_autostarts"] = int(ws.get("total_autostarts", 0)) + 1
            # Reset idle window so we do not spam duplicate work.
            ws["last_progress_unix"] = now
            ws["last_cycle_count"] = cycles
            log(f"AUTOSTART orchestration={new_orchestration_id} goal={goal}")
        except Exception as exc:
            action = "autostart_failed"
            log(f"ERROR autostart {type(exc).__name__}: {exc}\n{traceback.format_exc()}")

    # Advance cycle baseline periodically even while observing.
    if not should_start and delta_cycles >= DEFAULT_IDLE_CYCLES:
        ws["last_cycle_count"] = cycles

    ws["last_seen"] = {
        "state_path": str(p),
        "cycle_count": cycles,
        "completed_orchestrations": completed,
        "active_orchestrations": active,
        "failed_orchestrations": failed,
        "halted_orchestrations": halted,
        "running": running,
        "ready": ready,
        "idle_for_seconds": round(idle_for, 2),
        "delta_cycles": delta_cycles,
        "action": action,
        "new_orchestration_id": new_orchestration_id,
        "ts": now,
    }
    write_json(WATCHDOG_STATE, ws)
    return {"ok": True, **ws["last_seen"], "total_autostarts": ws["total_autostarts"]}

def main() -> None:
    interval = float(os.getenv("COMPANYOS_ANTISTALL_INTERVAL_SECONDS", "30"))
    log("START productive autonomy anti-stall watchdog")
    while True:
        try:
            result = tick()
            log("TICK " + json.dumps(result, sort_keys=True))
        except Exception as exc:
            log(f"FATAL_TICK {type(exc).__name__}: {exc}\n{traceback.format_exc()}")
        time.sleep(interval)

if __name__ == "__main__":
    main()
