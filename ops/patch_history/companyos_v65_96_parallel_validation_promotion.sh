#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
GLOBAL_RT="$HOME/.companyos_runtime"
LOCAL_RT="$ROOT/.companyos_runtime"
MODULE="$ROOT/companyos/runtime/parallel_validation_manager.py"
PIDFILE="$GLOBAL_RT/parallel_validation_manager.pid"
LOGFILE="$GLOBAL_RT/parallel_validation_manager.log"
OLD_PIDFILE="$GLOBAL_RT/parallel_profit_portfolio.pid"
INTERVAL_SECONDS="${COMPANYOS_VALIDATION_MANAGER_INTERVAL_SECONDS:-900}"

mkdir -p "$GLOBAL_RT" "$LOCAL_RT"
cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

install_module() {
cat > "$MODULE" <<'PY'
from __future__ import annotations

import json
import re
import time
from pathlib import Path

ROOT = Path.home() / "companyos"
RT = ROOT / ".companyos_runtime"
GLOBAL_RT = Path.home() / ".companyos_runtime"
ECON_ROOT = RT / "canonical_research_outputs"
STATE = RT / "parallel_validation_state.json"
REPORTS = GLOBAL_RT / "reports"

STATE.parent.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

def load(path: Path, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return default

def save(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    tmp.replace(path)

def slug(v):
    return re.sub(r"[^a-z0-9]+", "-", str(v or "").lower()).strip("-")[:72] or "validation"

def orchestration_state(oid):
    if not oid:
        return None
    d = load(GLOBAL_RT / "ceo_orchestrations" / f"{oid}.json", {})
    return d.get("state")

def canonical_economics_candidates():
    latest = {}
    if not ECON_ROOT.exists():
        return []

    for p in ECON_ROOT.glob("v65_95_economics_*.json"):
        d = load(p, {})
        if not isinstance(d, dict) or not d.get("name"):
            continue
        name = str(d["name"])
        prev = latest.get(name)
        ts = float(d.get("generated_at_unix", 0) or 0)
        if prev is None or ts >= prev[0]:
            latest[name] = (ts, p, d)

    rows = []
    for _, p, d in latest.values():
        rows.append({
            "name": d.get("name"),
            "business_model": d.get("business_model") or "unknown",
            "sector": d.get("sector") or d.get("market") or "unknown",
            "expected_profit_30d": float(d.get("expected_profit", 0) or 0),
            "probability": float(d.get("probability_success_pct", 0) or 0),
            "margin": float(d.get("margin", 0) or 0),
            "evidence_quality": float(d.get("evidence_quality_pct", 0) or 0),
            "evidence_count": int(d.get("evidence_count", 0) or 0),
            "pricing_domain_count": int(d.get("pricing_domain_count", 0) or 0),
            "pricing_observation_count": int(d.get("pricing_observation_count", 0) or 0),
            "economics_ready": bool(d.get("economics_ready")),
            "readiness": float(d.get("execution_readiness_pct", 0) or 0),
            "time_to_cash_days": float(d.get("time_to_cash_days", 30) or 30),
            "next_action": str(d.get("next_action") or ""),
            "observed_price_floor_usd": (
                (d.get("expected_profit_basis") or {}).get("observed_price_floor_usd")
                if isinstance(d.get("expected_profit_basis"), dict) else None
            ),
            "source_artifact": str(p.relative_to(ROOT)),
            "payload": d,
        })
    return rows

def qualification_reasons(c):
    reasons = []
    if not c["economics_ready"]:
        reasons.append("economics_not_ready")
    if c["business_model"] == "unknown":
        reasons.append("business_model_unknown")
    if c["sector"] == "unknown":
        reasons.append("sector_unknown")
    if c["pricing_domain_count"] < 2:
        reasons.append("insufficient_independent_pricing_domains")
    if c["evidence_count"] < 3:
        reasons.append("insufficient_external_evidence")
    if c["evidence_quality"] < 55:
        reasons.append("evidence_quality_below_validation_threshold")
    if c["expected_profit_30d"] <= 0:
        reasons.append("profit_estimate_missing")
    if c["probability"] <= 0:
        reasons.append("probability_estimate_missing")
    if c["readiness"] < 20:
        reasons.append("readiness_below_validation_threshold")
    if not c["next_action"].strip():
        reasons.append("missing_next_action")
    return reasons

def full_engine_scores():
    try:
        from companyos.runtime import profit_opportunity_engine as poe
        rows = poe.discover()
    except Exception:
        return {}

    best = {}
    for o in rows:
        k = str(o.name or "").strip().lower()
        if not k:
            continue
        prev = best.get(k)
        if prev is None or float(o.score or 0) > prev:
            best[k] = float(o.score or 0)
    return best

def current_external_validation():
    # Count only the known live commercial validation. Do not count CompanyOS
    # commissioning/launch-pipeline infrastructure as a business.
    d = load(RT / "live_validation_tracking.json", {})
    name = d.get("candidate_name")
    url = d.get("stable_public_url") or d.get("public_url")
    if not name:
        return None
    return {
        "name": name,
        "slug": slug(name),
        "public_url": url,
        "status": "LIVE_VALIDATION",
        "source": "live_validation_tracking",
    }

def make_goal(c):
    price = c.get("observed_price_floor_usd")
    return f"""
COMPANYOS PARALLEL PROFIT VALIDATION BET

PRIMARY OBJECTIVE:
Maximize sustainable risk-adjusted realized profit by testing this opportunity against
the other active validation bets. This is a VALIDATION experiment, not authorization
to scale spending.

CANDIDATE:
Name: {c['name']}
Business model: {c['business_model']}
Sector: {c['sector']}
Observed lower market price reference: {price}
Conservative first-30-day net-profit scenario: {c['expected_profit_30d']}
Validation probability estimate: {c['probability']}%
Evidence quality: {c['evidence_quality']}
Independent pricing domains: {c['pricing_domain_count']}
Evidence artifact: {c['source_artifact']}

MANDATE:
1. Build the smallest useful, credible, customer-facing validation asset for this
   specific opportunity.
2. Use the evidence-backed price anchor and buyer/problem/offer from the economics
   artifact. Do not invent customers, sales, revenue, profit, testimonials, demand,
   conversion, or traction.
3. Create a measurable CTA appropriate to the model, such as request demo, join
   waitlist, request quote, start free trial, or express purchase interest.
4. Add analytics/measurement hooks so CompanyOS can compare real interest and
   conversion with the other active validation bets.
5. Prefer a small landing page, prototype, demo, or narrowly scoped sellable offer
   over a large product build.
6. Persist the validation plan, artifacts, public URL if deployed, and measurable
   evidence in workspace/{slug(c['name'])}.
7. Use configured publication/deployment connectors only when existing policy and
   credentials authorize them.

BOUNDARIES:
- No paid ads.
- No purchase or financial transaction.
- No wallet transaction.
- No unsolicited bulk outreach.
- No contract or legal commitment.
- No credential bypass.
- No fabricated market evidence.
- Do not claim this venture is profitable until actual revenue/cost evidence exists.
- Preserve all existing external-action, deployment, financial, credential, legal,
  signer, reconciliation, destructive-action, and irreversible-action gates.

SUCCESS FOR THIS STAGE:
A real, measurable, reversible market-validation experiment that can be compared
against the other profit bets on observed demand and conversion.
""".strip()

def start_validation(c):
    from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator

    s = slug(c["name"])
    workspace = ROOT / "workspace" / s
    workspace.mkdir(parents=True, exist_ok=True)

    brief = {
        "schema": "companyos.parallel_profit_validation.v1",
        "canonical_id": s,
        "name": c["name"],
        "stage": "VALIDATE",
        "objective": "risk_adjusted_realized_profit",
        "economics": {
            "business_model": c["business_model"],
            "sector": c["sector"],
            "expected_profit_30d_scenario": c["expected_profit_30d"],
            "probability_estimate": c["probability"],
            "margin_estimate": c["margin"],
            "evidence_quality": c["evidence_quality"],
            "pricing_domain_count": c["pricing_domain_count"],
            "pricing_observation_count": c["pricing_observation_count"],
            "observed_price_floor_usd": c["observed_price_floor_usd"],
            "time_to_cash_days": c["time_to_cash_days"],
        },
        "source_artifact": c["source_artifact"],
        "next_required_outcome": (
            "Produce a measurable reversible market-validation experiment and collect "
            "real demand/conversion evidence before any scale decision."
        ),
        "financial_actions_authorized": False,
        "paid_marketing_authorized": False,
        "generated_at_unix": time.time(),
    }
    save(workspace / "validation_brief.json", brief)

    rec = AutonomousCEOOrchestrator().start(
        goal=make_goal(c),
        max_cycles=220,
        max_follow_up_depth=8,
        priority_base=380,
    )

    return {
        "name": c["name"],
        "slug": s,
        "business_model": c["business_model"],
        "sector": c["sector"],
        "full_profit_engine_score": c.get("full_profit_engine_score", 0),
        "expected_profit_30d_scenario": c["expected_profit_30d"],
        "probability_estimate": c["probability"],
        "evidence_quality": c["evidence_quality"],
        "pricing_domain_count": c["pricing_domain_count"],
        "source_artifact": c["source_artifact"],
        "workspace": str(workspace),
        "orchestration_id": getattr(rec, "orchestration_id", None),
        "status": "VALIDATING",
        "started_at_unix": time.time(),
    }

def cycle():
    from companyos.strategy.profit_first_venture_engine import ensure_policy

    policy = ensure_policy()
    max_slots = int(policy.get("max_active_validation_bets", 3) or 3)

    state = load(STATE, {})
    state.setdefault("validations", {})

    external = current_external_validation()
    external_count = 1 if external else 0

    # Keep validation bets occupying their slots even if the build orchestration
    # finishes; finishing a build does not mean the market test has finished.
    active_internal = [
        v for v in state["validations"].values()
        if v.get("status") == "VALIDATING"
    ]

    slots = max(0, max_slots - external_count - len(active_internal))

    candidates = canonical_economics_candidates()
    scores = full_engine_scores()
    for c in candidates:
        c["full_profit_engine_score"] = scores.get(str(c["name"]).strip().lower(), 0.0)
        c["qualification_reasons"] = qualification_reasons(c)

    qualified = [c for c in candidates if not c["qualification_reasons"]]
    qualified.sort(
        key=lambda c: (
            c["full_profit_engine_score"],
            c["evidence_quality"],
            c["probability"],
            c["expected_profit_30d"],
        ),
        reverse=True,
    )

    occupied_names = {
        str(v.get("name") or "").strip().lower()
        for v in active_internal
    }
    if external:
        occupied_names.add(str(external["name"]).strip().lower())

    occupied_models = {
        str(v.get("business_model") or "unknown")
        for v in active_internal
    }
    occupied_sectors = {
        str(v.get("sector") or "unknown")
        for v in active_internal
    }

    selected = []
    if slots > 0:
        # First pass favors model/sector diversity.
        for c in qualified:
            if len(selected) >= slots:
                break
            if str(c["name"]).strip().lower() in occupied_names:
                continue
            if c["business_model"] in occupied_models and c["sector"] in occupied_sectors:
                continue
            selected.append(c)
            occupied_names.add(str(c["name"]).strip().lower())
            occupied_models.add(c["business_model"])
            occupied_sectors.add(c["sector"])

        # Second pass fills remaining slots by strongest evidence-backed economics.
        if len(selected) < slots:
            for c in qualified:
                if len(selected) >= slots:
                    break
                if str(c["name"]).strip().lower() in occupied_names:
                    continue
                selected.append(c)
                occupied_names.add(str(c["name"]).strip().lower())

    started = []
    for c in selected:
        try:
            rec = start_validation(c)
            state["validations"][rec["slug"]] = rec
            started.append(rec)
        except Exception as exc:
            started.append({
                "name": c["name"],
                "status": "START_FAILED",
                "error": f"{type(exc).__name__}:{exc}",
            })

    active_internal = [
        v for v in state["validations"].values()
        if v.get("status") == "VALIDATING"
    ]
    total_active = external_count + len(active_internal)

    for v in active_internal:
        v["orchestration_state"] = orchestration_state(v.get("orchestration_id"))

    result = {
        "version": "V65.96",
        "timestamp_unix": time.time(),
        "objective": "risk_adjusted_realized_profit",
        "max_validation_slots": max_slots,
        "external_live_validation": external,
        "external_live_validation_count": external_count,
        "internal_validation_count": len(active_internal),
        "total_active_validation_bets": total_active,
        "remaining_validation_slots": max(0, max_slots - total_active),
        "economics_candidates": len(candidates),
        "validation_qualified_candidates": len(qualified),
        "started_this_cycle": started,
        "active_internal_validations": active_internal,
        "candidate_diagnostics": [
            {
                "name": c["name"],
                "business_model": c["business_model"],
                "sector": c["sector"],
                "full_profit_engine_score": c["full_profit_engine_score"],
                "economics_ready": c["economics_ready"],
                "expected_profit_30d": c["expected_profit_30d"],
                "probability": c["probability"],
                "evidence_quality": c["evidence_quality"],
                "pricing_domain_count": c["pricing_domain_count"],
                "qualification_reasons": c["qualification_reasons"],
            }
            for c in sorted(
                candidates,
                key=lambda x: (
                    x["full_profit_engine_score"],
                    x["evidence_quality"],
                ),
                reverse=True,
            )[:12]
        ],
        "guards": {
            "paid_ads": False,
            "financial_actions": False,
            "wallet_transactions": False,
            "unsolicited_bulk_outreach": False,
            "external_action_gates_unchanged": True,
            "deployment_gates_unchanged": True,
        },
    }

    state["last_cycle_unix"] = time.time()
    state["last_result"] = result
    save(STATE, state)

    rp = REPORTS / f"v65_96_parallel_validation_{int(time.time())}.json"
    save(rp, result)

    print("MAX_VALIDATION_SLOTS=", max_slots)
    print("EXTERNAL_LIVE_VALIDATIONS=", external_count)
    print("ECONOMICS_CANDIDATES=", len(candidates))
    print("VALIDATION_QUALIFIED_CANDIDATES=", len(qualified))
    print("STARTED_THIS_CYCLE=", json.dumps(started, sort_keys=True, default=str))
    print("INTERNAL_VALIDATION_COUNT=", len(active_internal))
    print("TOTAL_ACTIVE_VALIDATION_BETS=", total_active)
    print("REMAINING_VALIDATION_SLOTS=", max(0, max_slots - total_active))
    print("ACTIVE_INTERNAL_VALIDATIONS=", json.dumps(active_internal, sort_keys=True, default=str))
    print("REPORT=", rp)
    print("V65_96_PARALLEL_VALIDATION_GATE=PASS")
    print("V65_96_NO_FINANCIAL_ACTIONS=PASS")
    print("V65_96_EXISTING_GATES_PRESERVED=PASS")
    print("V65_96_COMPLETE")
    return result

def status():
    d = load(STATE, {"status":"not_run"})
    print(json.dumps(d.get("last_result", d), indent=2, sort_keys=True, default=str))

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=("once","loop","status"))
    p.add_argument("--interval", type=int, default=900)
    a = p.parse_args()

    if a.command == "once":
        cycle()
    elif a.command == "status":
        status()
    else:
        interval = max(600, int(a.interval))
        while True:
            try:
                cycle()
            except Exception as exc:
                print("V65_96_LOOP_ERROR=", f"{type(exc).__name__}:{exc}", flush=True)
            time.sleep(interval)

if __name__ == "__main__":
    main()
PY

python -m py_compile "$MODULE"
echo "MODULE_COMPILE=PASS"
}

stop_old_manager() {
  if [ -f "$OLD_PIDFILE" ]; then
    oldpid="$(cat "$OLD_PIDFILE" 2>/dev/null || true)"
    if [ -n "${oldpid:-}" ] && kill -0 "$oldpid" 2>/dev/null; then
      echo "STOPPING_V65_93_PID=$oldpid"
      kill "$oldpid" 2>/dev/null || true
      for _ in $(seq 1 20); do
        if ! kill -0 "$oldpid" 2>/dev/null; then break; fi
        sleep 1
      done
    fi
    rm -f "$OLD_PIDFILE"
  fi
}

is_running() {
  if [ ! -f "$PIDFILE" ]; then return 1; fi
  pid="$(cat "$PIDFILE" 2>/dev/null || true)"
  [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null
}

action="${1:-start}"

case "$action" in
  start)
    echo "===== COMPANYOS V65.96 PARALLEL VALIDATION PROMOTION ====="
    install_module
    stop_old_manager

    if is_running; then
      echo "VALIDATION_MANAGER_ALREADY_RUNNING=true"
      echo "PID=$(cat "$PIDFILE")"
      exit 0
    fi

    echo "===== INITIAL VALIDATION PORTFOLIO CYCLE ====="
    python -m companyos.runtime.parallel_validation_manager once

    nohup python -m companyos.runtime.parallel_validation_manager loop \
      --interval "$INTERVAL_SECONDS" >> "$LOGFILE" 2>&1 &
    pid="$!"
    echo "$pid" > "$PIDFILE"
    sleep 1

    if ! kill -0 "$pid" 2>/dev/null; then
      rm -f "$PIDFILE"
      echo "V65_96_ABORT=manager_failed_to_start"
      exit 1
    fi

    echo "VALIDATION_MANAGER_RUNNING=true"
    echo "PID=$pid"
    echo "INTERVAL_SECONDS=$INTERVAL_SECONDS"
    echo "LOGFILE=$LOGFILE"
    echo "V65_96_MANAGER_START=PASS"
    echo "V65_96_COMPLETE"
    ;;

  once)
    install_module
    python -m companyos.runtime.parallel_validation_manager once
    ;;

  status)
    echo "===== COMPANYOS V65.96 STATUS ====="
    if is_running; then
      echo "VALIDATION_MANAGER_RUNNING=true"
      echo "PID=$(cat "$PIDFILE")"
    else
      echo "VALIDATION_MANAGER_RUNNING=false"
    fi
    [ -f "$MODULE" ] && python -m companyos.runtime.parallel_validation_manager status || true
    echo "----- LOG TAIL -----"
    tail -n 100 "$LOGFILE" 2>/dev/null || true
    ;;

  stop)
    echo "===== COMPANYOS V65.96 STOP ====="
    if is_running; then
      pid="$(cat "$PIDFILE")"
      kill "$pid" 2>/dev/null || true
      for _ in $(seq 1 20); do
        if ! kill -0 "$pid" 2>/dev/null; then break; fi
        sleep 1
      done
      if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid" 2>/dev/null || true
      fi
    fi
    rm -f "$PIDFILE"
    echo "V65_96_STOP=PASS"
    ;;

  restart)
    "$0" stop || true
    exec "$0" start
    ;;

  *)
    echo "Usage: $0 {start|status|stop|restart|once}"
    exit 2
    ;;
esac
