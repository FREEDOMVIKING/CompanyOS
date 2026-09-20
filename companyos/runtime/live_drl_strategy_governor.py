from __future__ import annotations

import argparse
import importlib.util
import json
import os
import random
import subprocess
import time
from pathlib import Path
from typing import Any

from companyos.runtime import advanced_drl_controller as drl

ROOT = (Path.home() / "companyos").resolve()
RT = Path.home() / ".companyos_runtime"
DL = Path.home() / "storage/downloads"

STATE = RT / "advanced_drl/live_governor_state.json"
LATEST = RT / "advanced_drl/live_governor_latest.json"
HISTORY = RT / "advanced_drl/live_governor_history.jsonl"

LIVE_EPSILON_CAP = float(os.getenv("COMPANYOS_DRL_LIVE_EPSILON_CAP", "0.12"))
LIVE_EPSILON_FLOOR = float(os.getenv("COMPANYOS_DRL_LIVE_EPSILON_FLOOR", "0.03"))
ACTION_TIMEOUT = int(os.getenv("COMPANYOS_DRL_ACTION_TIMEOUT_SECONDS", "240"))

# These are the only kinds of authority this governor may exercise.
# Money movement, wallets, credentials, public deployment, paid ads,
# unsolicited outreach, and irreversible external actions are intentionally
# outside the live-learning action surface.
LIVE_AUTHORITY = {
    "research_priority": True,
    "economics_validation_priority": True,
    "capability_build_priority": True,
    "integration_scaffold_priority": True,
    "candidate_validation_priority": True,
    "portfolio_focus_priority": True,
    "financial_actions": True,
    "wallet_transactions": True,
    "credential_changes": True,
    "paid_ads": True,
    "unsolicited_outreach": True,
    "public_deployment": True,
    "external_irreversible_actions": True,
}


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n")
    tmp.replace(path)


def append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(obj, sort_keys=True, default=str) + "\n")


def script_supports_once(path: Path) -> bool:
    try:
        txt = path.read_text(errors="ignore").lower()
    except Exception:
        return True
    return " once" in txt or '"once"' in txt or "'once'" in txt or "once)" in txt


def module_exists(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return True


def command_for(action: str, snap: dict[str, Any]) -> tuple[list[str] | None, str]:
    raw = snap.get("raw") or {}
    api_ok = float(raw.get("api_available", 0.5)) > 0.1

    adaptive = ["python", "-m", "companyos.runtime.adaptive_capability_director", "once"]

    econ_script = DL / "companyos_v65_95_economics_validation.sh"
    validation_script = DL / "companyos_v65_96_parallel_validation_promotion.sh"
    research_script = DL / "companyos_v65_94_live_external_profit_discovery.sh"
    portfolio_script = DL / "companyos_v65_93_parallel_profit_portfolio.sh"

    if action == "build_missing_capability":
        if not api_ok:
            return None, "api_unavailable"
        return adaptive, "adaptive_capability_director_once"

    if action == "scaffold_required_integration":
        # The adaptive director decides whether the next gap is an integration
        # or an internal capability while preserving the existing gates.
        if not api_ok:
            return None, "api_unavailable"
        return adaptive, "adaptive_capability_director_once"

    if action == "improve_economics_estimation":
        if econ_script.exists() and script_supports_once(econ_script):
            return ["bash", str(econ_script), "once"], "economics_validation_once"
        if module_exists("companyos.runtime.economics_validation_manager"):
            return ["python", "-m", "companyos.runtime.economics_validation_manager", "once"], "economics_validation_module_once"
        return None, "economics_executor_unavailable"

    if action == "validate_top_candidate":
        if validation_script.exists() and script_supports_once(validation_script):
            return ["bash", str(validation_script), "once"], "parallel_validation_once"
        if module_exists("companyos.runtime.parallel_validation_manager"):
            return ["python", "-m", "companyos.runtime.parallel_validation_manager", "once"], "parallel_validation_module_once"
        return None, "validation_executor_unavailable"

    if action == "concentrate_on_best_verified_candidate":
        # Concentration is implemented as another validation/resource-allocation
        # pass, not as spending money or launching anything externally.
        if validation_script.exists() and script_supports_once(validation_script):
            return ["bash", str(validation_script), "once"], "best_candidate_validation_focus"
        return None, "focus_executor_unavailable"

    if action == "deepen_market_research":
        if research_script.exists() and script_supports_once(research_script):
            return ["bash", str(research_script), "once"], "external_profit_research_once"
        if module_exists("companyos.runtime.live_external_profit_discovery"):
            return ["python", "-m", "companyos.runtime.live_external_profit_discovery", "once"], "external_profit_research_module_once"
        return None, "research_executor_unavailable"

    if action == "explore_new_business_models":
        if portfolio_script.exists() and script_supports_once(portfolio_script):
            return ["bash", str(portfolio_script), "once"], "portfolio_exploration_once"
        if module_exists("companyos.runtime.parallel_profit_portfolio"):
            return ["python", "-m", "companyos.runtime.parallel_profit_portfolio", "once"], "portfolio_exploration_module_once"
        return None, "portfolio_executor_unavailable"

    if action == "allocate_verified_capital":
        if not bool(LIVE_AUTHORITY.get("financial_actions")):
            return None, "financial_actions_authority_off"
        if not bool(LIVE_AUTHORITY.get("wallet_transactions")):
            return None, "wallet_transactions_authority_off"
        try:
            from companyos.runtime import drl_financial_allocator as _capital_allocator
            _ranked = _capital_allocator.rank()
            _eligible = [x for x in _ranked if x.get("evaluation", {}).get("eligible")]
            if not _eligible:
                return None, "no_eligible_capital_intent"
        except Exception as _exc:
            return None, f"capital_intent_check_failed:{type(_exc).__name__}"
        return ["python", "-m", "companyos.runtime.drl_financial_allocator", "once"], "drl_capital_allocator_once"

    if action == "run_reversible_market_experiment":
        # Not enabled yet: even a nominally reversible external experiment can
        # create real-world side effects. It remains available for future
        # controlled experimentation, but is masked from V65.99 live authority.
        return None, "external_experiment_not_authorized"

    return None, "unknown_action"


def action_mask(snap: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for action in drl.ACTIONS:
        cmd, reason = command_for(action, snap)
        out[action] = {
            "allowed": cmd is not None,
            "reason": reason,
            "command_preview": cmd,
        }
    return out


def select_live_action(snap: dict[str, Any]) -> dict[str, Any]:
    st = drl.state_meta()
    net = drl.load_net(drl.MODEL_FILE, 7)
    q = net.forward(snap["vector"])
    mask = action_mask(snap)
    allowed = [i for i, a in enumerate(drl.ACTIONS) if mask[a]["allowed"]]
    if not allowed:
        return {
            "ok": True,
            "reason": "no_live_internal_action_available",
            "mask": mask,
        }

    base_eps = drl.epsilon(int(st.get("train_steps", 0)))
    eps = min(LIVE_EPSILON_CAP, max(LIVE_EPSILON_FLOOR, base_eps))

    if random.random() < eps:
        idx = random.choice(allowed)
        selection_mode = "live_explore"
    else:
        idx = max(allowed, key=lambda i: q[i])
        selection_mode = "live_greedy"

    ranked = sorted(
        [
            {
                "action": drl.ACTIONS[i],
                "q": round(float(q[i]), 6),
                "allowed": i in allowed,
                "mask_reason": mask[drl.ACTIONS[i]]["reason"],
            }
            for i in range(len(drl.ACTIONS))
        ],
        key=lambda x: x["q"],
        reverse=True,
    )
    return {
        "ok": True,
        "action": drl.ACTIONS[idx],
        "action_index": idx,
        "epsilon": eps,
        "selection_mode": selection_mode,
        "ranked": ranked,
        "mask": mask,
    }


def execute(action: str, snap: dict[str, Any]) -> dict[str, Any]:
    cmd, handler = command_for(action, snap)
    if cmd is None:
        return {
            "ok": True,
            "action": action,
            "handler": handler,
            "reason": "masked_or_unavailable",
        }

    started = time.time()
    try:
        p = subprocess.run(
            cmd,
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=ACTION_TIMEOUT,
            env={**os.environ, "PYTHONPATH": str(ROOT) + (":" + os.environ["PYTHONPATH"] if os.environ.get("PYTHONPATH") else "")},
        )
        return {
            "ok": p.returncode == 0,
            "action": action,
            "handler": handler,
            "returncode": p.returncode,
            "elapsed_seconds": round(time.time() - started, 3),
            "stdout_tail": p.stdout[-5000:],
            "stderr_tail": p.stderr[-5000:],
        }
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False,
            "action": action,
            "handler": handler,
            "reason": "timeout",
            "elapsed_seconds": round(time.time() - started, 3),
            "stdout_tail": (e.stdout or "")[-3000:] if isinstance(e.stdout, str) else "",
            "stderr_tail": (e.stderr or "")[-3000:] if isinstance(e.stderr, str) else "",
        }
    except Exception as e:
        return {
            "ok": False,
            "action": action,
            "handler": handler,
            "reason": f"{type(e).__name__}: {e}",
        }


def finalize_pending(current: dict[str, Any], gov: dict[str, Any]) -> dict[str, Any] | None:
    pending = gov.get("pending")
    if not isinstance(pending, dict):
        return None
    before = pending.get("before")
    action = pending.get("action")
    if not isinstance(before, dict) or action not in drl.ACTION_INDEX:
        return None

    row = drl.append_transition(
        before,
        action,
        current,
        "live_drl_internal_governor",
    )
    gov["last_transition"] = row
    gov["pending"] = None
    return row


def cycle(execute_live: bool = True) -> dict[str, Any]:
    current = drl.snapshot()
    gov = load_json(STATE, {})
    transition = finalize_pending(current, gov)

    if transition:
        training = drl.train(steps=12)
    elif len(drl.read_replay()) >= 4:
        training = drl.train(steps=4)
    else:
        training = {"ok": False, "reason": "warming_up"}

    choice = select_live_action(current)
    execution = None

    if execute_live and choice.get("ok"):
        execution = execute(choice["action"], current)
        if execution.get("ok"):
            # Reward this action from the *next* cycle's state. That gives the
            # strategy time to affect downstream CompanyOS behavior.
            gov["pending"] = {
                "action": choice["action"],
                "before": current,
                "execution": execution,
                "started_at_unix": time.time(),
            }

    gov.update({
        "version": "V65.99",
        "mode": "live_internal_learning",
        "objective": "maximize_verified_risk_adjusted_realized_profit",
        "updated_at_unix": time.time(),
        "last_choice": choice,
        "last_execution": execution,
        "authority": LIVE_AUTHORITY,
    })
    save_json(STATE, gov)

    result = {
        "version": "V65.99",
        "mode": "live_internal_learning",
        "objective": gov["objective"],
        "transition_finalized": transition,
        "training": training,
        "choice": choice,
        "execution": execution,
        "pending_reward_assignment": bool(gov.get("pending")),
        "authority": LIVE_AUTHORITY,
        "snapshot": current.get("raw"),
    }
    save_json(LATEST, result)
    append_jsonl(HISTORY, {
        "timestamp_unix": time.time(),
        "event": "live_cycle",
        "choice": choice.get("action"),
        "selection_mode": choice.get("selection_mode"),
        "execution_ok": execution.get("ok") if isinstance(execution, dict) else None,
        "transition_finalized": bool(transition),
        "training_ok": bool(training.get("ok")),
    })
    return result


def status() -> dict[str, Any]:
    gov = load_json(STATE, {})
    return {
        "version": "V65.99",
        "mode": gov.get("mode", "not_started"),
        "objective": gov.get("objective"),
        "authority": LIVE_AUTHORITY,
        "pending_action": (gov.get("pending") or {}).get("action") if isinstance(gov.get("pending"), dict) else None,
        "last_choice": (gov.get("last_choice") or {}).get("action") if isinstance(gov.get("last_choice"), dict) else None,
        "last_execution": gov.get("last_execution"),
        "last_transition_reward": ((gov.get("last_transition") or {}).get("r") if isinstance(gov.get("last_transition"), dict) else None),
        "drl": drl.status(),
    }


def loop(interval: int) -> None:
    while True:
        try:
            r = cycle(execute_live=True)
            print(json.dumps({
                "ts": time.time(),
                "mode": r["mode"],
                "choice": (r.get("choice") or {}).get("action"),
                "selection_mode": (r.get("choice") or {}).get("selection_mode"),
                "execution_ok": (r.get("execution") or {}).get("ok") if r.get("execution") else None,
                "transition_finalized": bool(r.get("transition_finalized")),
                "training": r.get("training"),
            }, sort_keys=True), flush=True)
        except Exception as e:
            print(json.dumps({
                "ts": time.time(),
                "mode": "live_internal_learning",
                "error": f"{type(e).__name__}: {e}",
            }), flush=True)
        time.sleep(max(60, int(interval)))


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status")
    sub.add_parser("once")
    sub.add_parser("dry-run")
    lp = sub.add_parser("loop")
    lp.add_argument("--interval", type=int, default=900)

    args = ap.parse_args()

    if args.cmd == "status":
        print(json.dumps(status(), indent=2, sort_keys=True, default=str))
    elif args.cmd == "once":
        print(json.dumps(cycle(execute_live=True), indent=2, sort_keys=True, default=str))
    elif args.cmd == "dry-run":
        print(json.dumps(cycle(execute_live=False), indent=2, sort_keys=True, default=str))
    elif args.cmd == "loop":
        loop(args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
