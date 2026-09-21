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
from companyos.runtime.research_to_execution_bridge import maybe_promote_candidate

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


def _producer_throttle_gate(bp: dict[str, Any], ws: dict[str, Any]) -> dict[str, Any]:
    # Convert AdaptiveBackpressure.producer_divisor into actual producer cadence.
    # Existing hard-stop behavior remains in force at the configured queue ceiling.
    snapshot = bp.get("snapshot") if isinstance(bp, dict) else {}
    snapshot = snapshot if isinstance(snapshot, dict) else {}

    queued = int(snapshot.get("queued", 0) or 0)
    divisor = max(1, int((bp or {}).get("producer_divisor", 1) or 1))
    hard_threshold = int(os.getenv("COMPANYOS_BACKPRESSURE_QUEUE_THRESHOLD", "300"))

    tick = int(ws.get("backpressure_producer_tick", 0) or 0) + 1
    ws["backpressure_producer_tick"] = tick

    if queued >= hard_threshold:
        return {
            "allow_producer": False,
            "action": "backpressure_execution_first",
            "queued": queued,
            "producer_divisor": divisor,
            "producer_tick": tick,
            "hard_threshold": hard_threshold,
        }

    allow = ((tick - 1) % divisor) == 0
    return {
        "allow_producer": allow,
        "action": "producer_allowed" if allow else "backpressure_producer_throttled",
        "queued": queued,
        "producer_divisor": divisor,
        "producer_tick": tick,
        "hard_threshold": hard_threshold,
    }


def _profit_first_candidate_count() -> int:
    dirs = [
        RUNTIME / "profit_first_candidates",
        Path.home() / ".companyos_runtime" / "profit_first_candidates",
    ]
    seen: set[str] = set()
    for d in dirs:
        try:
            if d.exists():
                for p in d.glob("*.json"):
                    seen.add(str(p))
        except Exception:
            pass
    return len(seen)


def _profit_first_orchestration_record(orchestration_id: str | None) -> dict[str, Any]:
    if not orchestration_id:
        return {}
    for p in (
        Path.home() / ".companyos_runtime" / "ceo_orchestrations" / f"{orchestration_id}.json",
        RUNTIME / "ceo_orchestrations" / f"{orchestration_id}.json",
    ):
        if p.exists():
            d = read_json(p)
            if d:
                d["_record_path"] = str(p)
                return d
    return {}


def _clear_profit_first_producer_owner(ws: dict[str, Any]) -> None:
    for key in (
        "profit_first_producer_owner_name",
        "profit_first_producer_owner_orchestration_id",
        "profit_first_producer_owner_started_unix",
        "profit_first_producer_owner_candidate_count_baseline",
        "profit_first_producer_owner_timeout_seconds",
    ):
        ws.pop(key, None)


def _profit_first_producer_owner_state(ws: dict[str, Any], *, timeout_seconds: int) -> dict[str, Any]:
    """V69.11 outcome-aware profit-first producer ownership.

    Candidate materialization by itself does not release a RUNNING owner.
    Ownership releases only on a terminal orchestration state or bounded timeout.
    """
    oid = str(ws.get("profit_first_producer_owner_orchestration_id") or "")
    name = str(ws.get("profit_first_producer_owner_name") or "")
    started = float(ws.get("profit_first_producer_owner_started_unix", 0) or 0)
    baseline = int(ws.get("profit_first_producer_owner_candidate_count_baseline", 0) or 0)
    now = time.time()
    current = _profit_first_candidate_count()
    if not oid:
        return {"blocking": False, "reason": "no_profit_first_producer_owner", "candidate_count": current}

    rec = _profit_first_orchestration_record(oid)
    state = str(rec.get("state") or "UNKNOWN").upper()
    age = max(0.0, now - started) if started else 0.0
    delta = current - baseline
    terminal = state in {"COMPLETED", "FAILED", "HALTED", "CANCELLED"}

    if terminal or (started and age >= timeout_seconds):
        outcome = (
            ("terminal_with_candidates" if delta > 0 else "terminal_without_candidates")
            if terminal else "owner_timeout"
        )
        ws["profit_first_producer_last_owner_outcome"] = outcome
        ws["profit_first_producer_last_owner_terminal_state"] = state
        ws["profit_first_producer_last_owner_orchestration_id"] = oid
        ws["profit_first_producer_last_owner_name"] = name
        ws["profit_first_producer_last_owner_age_seconds"] = round(age, 3)
        ws["profit_first_producer_last_owner_candidate_delta"] = delta
        ws["profit_first_producer_last_owner_released_unix"] = now
        _clear_profit_first_producer_owner(ws)
        write_json(WATCHDOG_STATE, ws)
        return {
            "blocking": False, "reason": outcome, "owner_name": name,
            "orchestration_id": oid, "state": state, "age_seconds": age,
            "candidate_count": current, "candidate_delta": delta,
            "record_path": rec.get("_record_path"),
        }

    return {
        "blocking": True, "reason": "active_profit_first_producer_owner",
        "owner_name": name, "orchestration_id": oid, "state": state,
        "age_seconds": age, "timeout_seconds": timeout_seconds,
        "candidate_count": current, "candidate_delta": delta,
        "record_path": rec.get("_record_path"),
    }


def _claim_profit_first_producer_owner(
    ws: dict[str, Any], *, name: str, result: dict[str, Any],
    timeout_seconds: int, candidate_count_baseline: int,
) -> None:
    oid = str(result.get("orchestration_id") or "")
    if not oid:
        return
    now = time.time()
    ws["profit_first_producer_owner_name"] = name
    ws["profit_first_producer_owner_orchestration_id"] = oid
    ws["profit_first_producer_owner_started_unix"] = now
    ws["profit_first_producer_owner_candidate_count_baseline"] = int(candidate_count_baseline)
    ws["profit_first_producer_owner_timeout_seconds"] = int(timeout_seconds)
    ws["profit_first_producer_last_dispatch_unix"] = now
    ws["profit_first_producer_last_name"] = name
    ws["profit_first_producer_last_orchestration_id"] = oid
    write_json(WATCHDOG_STATE, ws)


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

def _v49_backpressure():
    try:
        from companyos.runtime.adaptive_backpressure import AdaptiveBackpressure
        return AdaptiveBackpressure().decide()
    except Exception:
        return {"snapshot": {"queued": 0}, "producer_divisor": 1}

def tick() -> dict[str, Any]:
    bp = _v49_backpressure()
    ws = watchdog_state()
    gate = _producer_throttle_gate(bp, ws)

    # Persist cadence state on each watchdog tick so adaptive throttling is
    # stable across repeated observations and process restarts.
    write_json(WATCHDOG_STATE, ws)

    if not gate["allow_producer"]:
        p, rs = runtime_state()
        ws["last_seen"] = {
            "state_path": str(p) if p else None,
            "action": gate["action"],
            "queued": gate["queued"],
            "producer_divisor": gate["producer_divisor"],
            "producer_tick": gate["producer_tick"],
            "hard_threshold": gate["hard_threshold"],
            "ts": time.time(),
        }
        write_json(WATCHDOG_STATE, ws)
        return {"ok": True, **ws["last_seen"]}
    promotion = maybe_promote_candidate(
        min_score=float(os.getenv("COMPANYOS_EXECUTION_PROMOTION_MIN_SCORE", "45")),
        cooldown_seconds=int(os.getenv("COMPANYOS_EXECUTION_PROMOTION_COOLDOWN_SECONDS", "900")),
        max_existing_execution_ventures=int(os.getenv("COMPANYOS_MAX_ACTIVE_EXECUTION_VENTURES", "3")),
    )
    if promotion.get("started"):
        log("RESEARCH_TO_EXECUTION_PROMOTION " + json.dumps(promotion, default=str, sort_keys=True))

    execution_backlog = (
        promotion.get("started")
        or int(promotion.get("eligible_count", 0) or 0) > 0
        or promotion.get("reason") in {"execution_capacity_full", "promotion_cooldown"}
    )

    # V69.11 outcome-aware profit-first producer ownership.
    producer_handoff_seconds = max(
        15,
        int(os.getenv("COMPANYOS_PROFIT_FIRST_PRODUCER_HANDOFF_COOLDOWN_SECONDS", "60")),
    )
    producer_owner_timeout_seconds = max(
        producer_handoff_seconds,
        int(os.getenv("COMPANYOS_PROFIT_FIRST_PRODUCER_OWNER_TIMEOUT_SECONDS", "600")),
    )

    owner_state = _profit_first_producer_owner_state(
        ws, timeout_seconds=producer_owner_timeout_seconds,
    )
    owner_blocking = bool(owner_state.get("blocking"))
    ws["profit_first_producer_owner_observation"] = owner_state
    write_json(WATCHDOG_STATE, ws)

    producer_now = time.time()
    producer_last_dispatch = float(ws.get("profit_first_producer_last_dispatch_unix", 0) or 0)
    producer_handoff_remaining = max(
        0.0, producer_handoff_seconds - (producer_now - producer_last_dispatch),
    )
    producer_window_open = (
        not execution_backlog and not owner_blocking and producer_handoff_remaining <= 0.0
    )
    producer_dispatched_this_tick = False

    def _record_profit_first_producer(
        name: str, result: dict[str, Any], *, candidate_count_baseline: int,
    ) -> None:
        nonlocal producer_dispatched_this_tick, producer_last_dispatch, owner_blocking
        producer_dispatched_this_tick = True
        producer_last_dispatch = time.time()
        _claim_profit_first_producer_owner(
            ws, name=name, result=result,
            timeout_seconds=producer_owner_timeout_seconds,
            candidate_count_baseline=candidate_count_baseline,
        )
        owner_blocking = bool(result.get("orchestration_id"))
        ws["profit_first_producer_handoff_seconds"] = producer_handoff_seconds
        write_json(WATCHDOG_STATE, ws)

    if execution_backlog:
        profit_first_enrichment_expansion = {"started": False, "reason": "execution_backlog_preferred_over_more_research"}
    elif owner_blocking:
        profit_first_enrichment_expansion = {"started": False, "reason": "active_profit_first_producer_owner", "owner": owner_state}
    elif not producer_window_open:
        profit_first_enrichment_expansion = {
            "started": False, "reason": "shared_profit_first_producer_handoff_cooldown",
            "cooldown_remaining_seconds": round(producer_handoff_remaining, 2),
        }
    else:
        baseline = _profit_first_candidate_count()
        profit_first_enrichment_expansion = maybe_run_profit_first_enrichment_expansion(
            cooldown_seconds=int(os.getenv("COMPANYOS_PROFIT_FIRST_ENRICHMENT_COOLDOWN_SECONDS", "300")),
        )
        if profit_first_enrichment_expansion.get("started"):
            _record_profit_first_producer(
                "profit_first_enrichment_expansion", profit_first_enrichment_expansion,
                candidate_count_baseline=baseline,
            )
            log("PROFIT_FIRST_ENRICHMENT_EXPANSION " + json.dumps(profit_first_enrichment_expansion, default=str, sort_keys=True))

    candidate_materialization = materialize_profit_first_candidates()
    if candidate_materialization.get("candidate_files_written_or_updated", 0) > 0:
        log("PROFIT_FIRST_CANDIDATES_MATERIALIZED " + json.dumps(candidate_materialization, default=str, sort_keys=True))

    producer_handoff_remaining = max(
        0.0, producer_handoff_seconds - (time.time() - producer_last_dispatch),
    )
    if execution_backlog:
        candidate_recovery = {"started": False, "reason": "execution_backlog_preferred_over_more_research"}
    elif owner_blocking or producer_dispatched_this_tick:
        candidate_recovery = {"started": False, "reason": "active_profit_first_producer_owner", "owner": owner_state}
    elif producer_handoff_remaining > 0.0:
        candidate_recovery = {
            "started": False, "reason": "shared_profit_first_producer_handoff_cooldown",
            "cooldown_remaining_seconds": round(producer_handoff_remaining, 2),
        }
    else:
        baseline = _profit_first_candidate_count()
        candidate_recovery = maybe_recover_profit_first_outputs(
            min_expected_candidates=1,
            cooldown_seconds=int(os.getenv("COMPANYOS_CANDIDATE_RECOVERY_COOLDOWN_SECONDS", "300")),
        )
        if candidate_recovery.get("started"):
            _record_profit_first_producer(
                "candidate_recovery", candidate_recovery,
                candidate_count_baseline=baseline,
            )
            log("PROFIT_FIRST_CANDIDATE_RECOVERY " + json.dumps(candidate_recovery, default=str, sort_keys=True))

    producer_handoff_remaining = max(
        0.0, producer_handoff_seconds - (time.time() - producer_last_dispatch),
    )
    if execution_backlog:
        profit_first_research = {"started": False, "reason": "execution_backlog_preferred_over_more_research"}
    elif owner_blocking or producer_dispatched_this_tick:
        profit_first_research = {"started": False, "reason": "active_profit_first_producer_owner", "owner": owner_state}
    elif producer_handoff_remaining > 0.0:
        profit_first_research = {
            "started": False, "reason": "shared_profit_first_producer_handoff_cooldown",
            "cooldown_remaining_seconds": round(producer_handoff_remaining, 2),
        }
    else:
        baseline = _profit_first_candidate_count()
        profit_first_research = maybe_run_profit_first_research(
            cooldown_seconds=int(os.getenv("COMPANYOS_PROFIT_FIRST_RESEARCH_COOLDOWN_SECONDS", "300")),
        )
        if profit_first_research.get("started"):
            _record_profit_first_producer(
                "profit_first_research", profit_first_research,
                candidate_count_baseline=baseline,
            )
            log("PROFIT_FIRST_RESEARCH " + json.dumps(profit_first_research, default=str, sort_keys=True))

    if execution_backlog:
        profit_first_dispatch = {
            "started": False,
            "reason": "execution_backlog_preferred_over_more_research",
        }
    else:
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
