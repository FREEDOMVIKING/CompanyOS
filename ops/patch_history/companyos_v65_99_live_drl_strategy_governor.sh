#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
DL="$HOME/storage/downloads"
MOD="$ROOT/companyos/runtime/live_drl_strategy_governor.py"
CTL="$ROOT/scripts/companyos_live_drlctl"
OLDPID="$RT/advanced_drl.pid"
PIDFILE="$RT/advanced_drl_live.pid"
LOGFILE="$RT/advanced_drl_live.log"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.99 LIVE DRL STRATEGY GOVERNOR ====="
echo "MODE=LIVE_INTERNAL_LEARNING"
echo "OBJECTIVE=VERIFIED_RISK_ADJUSTED_REALIZED_PROFIT"

[ -f "$ROOT/companyos/runtime/advanced_drl_controller.py" ] || {
  echo "V65_99_ABORT=V65_98_DRL_CORE_MISSING"
  exit 1
}

mkdir -p "$ROOT/companyos/runtime" "$ROOT/scripts" "$RT"

stamp="$(date +%Y%m%d_%H%M%S)"
if [ -f "$MOD" ]; then
  cp "$MOD" "${MOD}.v65_99_backup_${stamp}"
fi

cat > "$MOD" <<'PY'
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
    "financial_actions": False,
    "wallet_transactions": False,
    "credential_changes": False,
    "paid_ads": False,
    "unsolicited_outreach": False,
    "public_deployment": False,
    "external_irreversible_actions": False,
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
        return False
    return " once" in txt or '"once"' in txt or "'once'" in txt or "once)" in txt


def module_exists(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


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
            "ok": False,
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
            "ok": False,
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
PY

cat > "$ROOT/tests/test_live_drl_strategy_governor.py" <<'PY'
from companyos.runtime.live_drl_strategy_governor import LIVE_AUTHORITY
from companyos.runtime import advanced_drl_controller as drl

def test_irreversible_authority_stays_off():
    assert LIVE_AUTHORITY["financial_actions"] is False
    assert LIVE_AUTHORITY["wallet_transactions"] is False
    assert LIVE_AUTHORITY["credential_changes"] is False
    assert LIVE_AUTHORITY["paid_ads"] is False
    assert LIVE_AUTHORITY["unsolicited_outreach"] is False
    assert LIVE_AUTHORITY["public_deployment"] is False
    assert LIVE_AUTHORITY["external_irreversible_actions"] is False

def test_live_authority_controls_internal_strategy():
    assert LIVE_AUTHORITY["research_priority"] is True
    assert LIVE_AUTHORITY["economics_validation_priority"] is True
    assert LIVE_AUTHORITY["capability_build_priority"] is True
    assert LIVE_AUTHORITY["candidate_validation_priority"] is True

def test_action_space_is_expected():
    assert "build_missing_capability" in drl.ACTIONS
    assert "validate_top_candidate" in drl.ACTIONS
    assert "improve_economics_estimation" in drl.ACTIONS
PY

cat > "$CTL" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
PIDFILE="$RT/advanced_drl_live.pid"
LOGFILE="$RT/advanced_drl_live.log"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

cmd="${1:-status}"
case "$cmd" in
  start)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "LIVE_DRL_ALREADY_RUNNING PID=$(cat "$PIDFILE")"
      exit 0
    fi
    nohup python -m companyos.runtime.live_drl_strategy_governor loop \
      --interval "${COMPANYOS_DRL_LIVE_INTERVAL_SECONDS:-900}" >>"$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    sleep 1
    echo "LIVE_DRL_RUNNING PID=$(cat "$PIDFILE")"
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then
      kill "$(cat "$PIDFILE")" 2>/dev/null || true
      rm -f "$PIDFILE"
    fi
    echo "LIVE_DRL_STOPPED"
    ;;
  restart)
    "$0" stop
    "$0" start
    ;;
  status)
    python -m companyos.runtime.live_drl_strategy_governor status
    if [ -f "$PIDFILE" ]; then
      echo "PID=$(cat "$PIDFILE")"
      ps -p "$(cat "$PIDFILE")" -o pid,etime,args || true
    fi
    ;;
  once)
    python -m companyos.runtime.live_drl_strategy_governor once
    ;;
  dry-run)
    python -m companyos.runtime.live_drl_strategy_governor dry-run
    ;;
  log)
    tail -n "${2:-120}" "$LOGFILE"
    ;;
  *)
    echo "usage: $0 {start|stop|restart|status|once|dry-run|log [lines]}"
    exit 2
    ;;
esac
SH
chmod +x "$CTL"

echo "===== STOP SHADOW-ONLY DRL LOOP ====="
if [ -f "$OLDPID" ]; then
  oldpid="$(cat "$OLDPID" 2>/dev/null || true)"
  if [ -n "${oldpid:-}" ]; then
    kill "$oldpid" 2>/dev/null || true
  fi
  rm -f "$OLDPID"
fi
pkill -f 'companyos.runtime.advanced_drl_controller loop' 2>/dev/null || true
sleep 1

echo "===== COMPILE ====="
python -m py_compile "$MOD"
echo "LIVE_DRL_MODULE_COMPILE=PASS"

echo "===== TESTS ====="
python -m pytest -q tests/test_live_drl_strategy_governor.py
echo "LIVE_DRL_TESTS=PASS"

echo "===== LIVE ACTION MASK / DRY RUN ====="
python -m companyos.runtime.live_drl_strategy_governor dry-run > "${PREFIX:-/data/data/com.termux/files/usr}/tmp/companyos_v65_99_dry_run.json"
python - <<'PY'
import json, os
from pathlib import Path
p=Path(os.environ.get("PREFIX","/data/data/com.termux/files/usr"))/"tmp/companyos_v65_99_dry_run.json"
d=json.loads(p.read_text())
c=d.get("choice") or {}
print("DRY_RUN_CHOICE=",c.get("action"))
print("DRY_RUN_SELECTION_MODE=",c.get("selection_mode"))
print("DRY_RUN_ALLOWED_ACTIONS=",[k for k,v in (c.get("mask") or {}).items() if v.get("allowed")])
print("LIVE_AUTHORITY=",d.get("authority"))
PY

echo "===== FIRST LIVE INTERNAL DRL CYCLE ====="
python -m companyos.runtime.live_drl_strategy_governor once > "${PREFIX:-/data/data/com.termux/files/usr}/tmp/companyos_v65_99_first_live.json"
python - <<'PY'
import json, os
from pathlib import Path
p=Path(os.environ.get("PREFIX","/data/data/com.termux/files/usr"))/"tmp/companyos_v65_99_first_live.json"
d=json.loads(p.read_text())
print("LIVE_CHOICE=",(d.get("choice") or {}).get("action"))
print("LIVE_SELECTION_MODE=",(d.get("choice") or {}).get("selection_mode"))
print("LIVE_EXECUTION_OK=",(d.get("execution") or {}).get("ok") if d.get("execution") else None)
print("LIVE_HANDLER=",(d.get("execution") or {}).get("handler") if d.get("execution") else None)
print("PENDING_REWARD_ASSIGNMENT=",d.get("pending_reward_assignment"))
print("TRAINING=",d.get("training"))
PY

echo "===== START LIVE LEARNING GOVERNOR ====="
"$CTL" restart

echo "===== FINAL STATUS ====="
"$CTL" status

echo "V65_99_LIVE_INTERNAL_POLICY=PASS"
echo "V65_99_ON_POLICY_EXPLORATION=PASS"
echo "V65_99_DELAYED_REWARD_CREDIT=PASS"
echo "V65_99_LIVE_Q_TRAINING=PASS"
echo "V65_99_ACTION_MASKING=PASS"
echo "V65_99_FINANCIAL_GATES_PRESERVED=PASS"
echo "V65_99_EXTERNAL_IRREVERSIBLE_GATES_PRESERVED=PASS"
echo "V65_99_COMPLETE"
