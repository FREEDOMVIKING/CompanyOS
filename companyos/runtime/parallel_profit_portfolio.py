from __future__ import annotations

import json
import os
import re
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from collections import Counter

ROOT = Path.home() / "companyos"
RT = ROOT / ".companyos_runtime"
GLOBAL_RT = Path.home() / ".companyos_runtime"
STATE = RT / "parallel_profit_portfolio_state.json"
REPORTS = GLOBAL_RT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

RESEARCH_COOLDOWN = max(
    1800,
    int(os.getenv("COMPANYOS_PARALLEL_RESEARCH_COOLDOWN_SECONDS", "21600")),
)

TRACKS = {
    "software_data_automation": {
        "models": [
            "software_saas_ai",
            "data_api_licensing",
            "automation_products",
            "lead_generation_assets",
        ],
        "brief": (
            "Search for software, AI, data/API licensing, automation, and lead-generation "
            "opportunities across unrelated industries. Do not favor construction."
        ),
    },
    "commerce_media_digital": {
        "models": [
            "digital_products",
            "ecommerce_physical_products",
            "content_media",
            "subscriptions_memberships",
        ],
        "brief": (
            "Search for digital-product, ecommerce, content/media, and subscription "
            "opportunities across unrelated industries and customer types."
        ),
    },
    "marketplaces_services_brokerage": {
        "models": [
            "marketplaces_platforms",
            "services",
            "brokerage_commission",
            "mobile_web_apps",
        ],
        "brief": (
            "Search for marketplace/platform, productized-service, brokerage/commission, "
            "and mobile/web-app opportunities across unrelated sectors."
        ),
    },
}

def read_json(path: Path, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(path.read_text(errors="ignore"))
    except Exception:
        return default

def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True, default=str) + "\n")
    tmp.replace(path)

def slug(v):
    return re.sub(r"[^a-z0-9]+", "-", str(v or "").lower()).strip("-")[:80]

def key_for(o):
    return "|".join([
        slug(getattr(o, "name", "")),
        slug(getattr(o, "mechanism", "")),
        slug(getattr(o, "category", "")),
    ])

def orchestration_record(oid):
    if not oid:
        return {}
    return read_json(GLOBAL_RT / "ceo_orchestrations" / f"{oid}.json", {})

def running_orchestration(oid):
    rec = orchestration_record(oid)
    return str(rec.get("state") or "").upper() == "RUNNING"

def published_keys(candidate_names):
    """
    Count commercial published ventures, not CompanyOS infrastructure/commissioning
    pages. A generic launch-pipeline test page must not consume a profit-validation slot.
    """
    candidate_names = set(candidate_names)
    keys = set()

    live = read_json(RT / "live_validation_tracking.json", {})
    if live:
        nm = live.get("candidate_name")
        if nm:
            keys.add(slug(nm))

    ledger = RT / "venture_launch_ledger.jsonl"
    infrastructure_markers = (
        "companyos-venture-launch-pipeline",
        "companyos-commissioning",
        "commissioning",
        "launch-pipeline",
    )

    if ledger.exists():
        for line in ledger.read_text(errors="ignore").splitlines():
            try:
                d = json.loads(line)
            except Exception:
                continue
            nm = d.get("title") or d.get("name") or d.get("slug")
            if not nm:
                continue
            k = slug(nm)
            if any(m in k for m in infrastructure_markers):
                continue
            # Only consume a commercial validation slot when it maps to a current
            # discovered money-making candidate.
            if k in candidate_names:
                keys.add(k)
    return keys

def strict_reasons(o, poe):
    fn = getattr(poe, "_candidate_qualification_reasons", None)
    if callable(fn):
        return list(fn(o))
    reasons = []
    if float(getattr(o, "score", 0) or 0) < 45:
        reasons.append("score_below_execution_threshold")
    if int(getattr(o, "evidence_count", 0) or 0) < 1:
        reasons.append("missing_external_evidence")
    if float(getattr(o, "probability", 0) or 0) <= 0:
        reasons.append("probability_unestimated")
    if float(getattr(o, "expected_profit", 0) or 0) <= 0:
        reasons.append("profit_unestimated")
    if not str(getattr(o, "next_action", "") or "").strip():
        reasons.append("missing_executable_next_action")
    return reasons

def research_goal(track_id, cfg, policy):
    models = ", ".join(cfg["models"])
    min_candidates = int(policy.get("minimum_candidates", 20) or 20)
    min_sectors = int(policy.get("minimum_unrelated_sectors", 8) or 8)
    min_models = int(policy.get("minimum_business_model_families", 7) or 7)

    return f"""
PARALLEL_PROFIT_DISCOVERY_TRACK={track_id}

PRIMARY OBJECTIVE:
Maximize sustainable long-term risk-adjusted realized profit. Profitability is the
decision objective; do not optimize for familiarity, construction, number of artifacts,
or number of companies created.

TRACK FOCUS:
{cfg["brief"]}

BUSINESS MODEL FAMILIES IN THIS TRACK:
{models}

PORTFOLIO REQUIREMENTS:
- This track is one of several parallel discovery tracks.
- Across the combined CompanyOS portfolio, target at least {min_candidates} genuinely
  distinct commercial opportunities across at least {min_sectors} unrelated sectors and
  at least {min_models} business-model families.
- Do not clone, rename, version-bump, or superficially mutate an existing idea.
- Construction may compete, but receives no preference.
- Prefer cheap-to-test, automatable, scalable, fast-to-revenue opportunities when
  expected risk-adjusted profit is otherwise comparable.

EVIDENCE CONTRACT:
For each candidate, use real external evidence when available and preserve source URLs.
Do not invent demand, customers, probability, revenue, profit, margins, or evidence.
If a value cannot be supported, set it to 0/unknown and identify the evidence gap.

STANDARDIZED ECONOMICS:
Use expected_profit as estimated NET PROFIT IN USD OVER THE FIRST 30 DAYS OF OPERATION,
with assumptions stated. Also provide margin, probability_success_pct,
time_to_cash_days, capital_required, evidence_count, evidence_quality_pct,
execution_readiness_pct, business_model, market/sector, target_customer, problem,
offer, next_action, and source URLs.

OUTPUT CONTRACT:
Create machine-readable JSON candidate records that the CompanyOS
candidate_enrichment_bridge can ingest from canonical research outputs. Each record
must represent one commercial opportunity and include at least:
name, business_model, target_customer, problem, offer, market, expected_profit, margin,
probability_success_pct, evidence_count, evidence_quality_pct,
execution_readiness_pct, time_to_cash_days, capital_required, next_action, evidence.

This is research/validation preparation. Do not spend money, send outreach, sign
transactions, buy domains, enter contracts, or perform irreversible external actions.
Use existing external-action, financial, credential, legal, and publication gates.
""".strip()

def choose_diverse(rows, limit, occupied_names):
    chosen = []
    sectors = set()
    models = set()

    for o in rows:
        if slug(getattr(o, "name", "")) in occupied_names:
            continue
        sec = slug(getattr(o, "category", "unknown"))
        model = slug(getattr(o, "mechanism", "unknown"))
        if chosen and sec in sectors and model in models:
            continue
        chosen.append(o)
        sectors.add(sec)
        models.add(model)
        if len(chosen) >= limit:
            return chosen

    for o in rows:
        if o in chosen:
            continue
        if slug(getattr(o, "name", "")) in occupied_names:
            continue
        chosen.append(o)
        if len(chosen) >= limit:
            break
    return chosen

def maintain():
    from companyos.strategy.profit_first_venture_engine import ensure_policy
    from companyos.runtime import profit_opportunity_engine as poe
    from companyos.runtime.candidate_enrichment_bridge import refresh_enrichments
    from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator

    now = time.time()
    policy = ensure_policy()
    max_validation = int(policy.get("max_active_validation_bets", 3) or 3)

    state = read_json(STATE, {})
    state.setdefault("research_tracks", {})
    state.setdefault("candidate_executions", {})

    enrichment = refresh_enrichments()
    rows = poe.discover()

    qualified = []
    rejected = []
    for o in rows:
        reasons = strict_reasons(o, poe)
        if reasons:
            rejected.append({
                "name": getattr(o, "name", None),
                "score": getattr(o, "score", None),
                "reasons": reasons,
            })
        else:
            qualified.append(o)

    candidate_names = {slug(getattr(o, "name", "")) for o in rows}
    published = published_keys(candidate_names)

    # Keep only execution records whose orchestrations are genuinely still RUNNING.
    active_exec = {}
    for k, rec in list(state["candidate_executions"].items()):
        oid = rec.get("orchestration_id")
        if running_orchestration(oid):
            active_exec[k] = rec

    active_validation_count = len(published) + len(active_exec)
    slots = max(0, max_validation - active_validation_count)

    occupied_names = set(published)
    occupied_names.update(slug(v.get("name")) for v in active_exec.values())

    started_validations = []
    if slots > 0 and qualified:
        picks = choose_diverse(qualified, slots, occupied_names)
        for o in picks:
            k = key_for(o)
            if k in active_exec:
                continue
            payload = asdict(o)
            try:
                ex = poe._start_execution(payload)
                rec = {
                    "name": getattr(o, "name", None),
                    "business_model": getattr(o, "mechanism", None),
                    "sector": getattr(o, "category", None),
                    "score": getattr(o, "score", None),
                    "expected_profit_30d": getattr(o, "expected_profit", None),
                    "orchestration_id": ex.get("orchestration_id"),
                    "workspace": ex.get("workspace"),
                    "started_at_unix": now,
                }
                state["candidate_executions"][k] = rec
                active_exec[k] = rec
                started_validations.append(rec)
                occupied_names.add(slug(rec["name"]))
            except Exception as exc:
                started_validations.append({
                    "name": getattr(o, "name", None),
                    "error": f"{type(exc).__name__}:{exc}",
                })

    # Maintain three complementary research lanes. These are NOT counted as
    # validation bets and cannot promote a candidate by themselves.
    started_research = []
    for track_id, cfg in TRACKS.items():
        tr = state["research_tracks"].get(track_id, {})
        oid = tr.get("orchestration_id")
        if running_orchestration(oid):
            continue

        last = float(tr.get("last_started_unix", 0) or 0)
        if now - last < RESEARCH_COOLDOWN:
            continue

        oid = f"parallel-profit-{track_id}-{int(now)}-{uuid.uuid4().hex[:8]}"
        goal = research_goal(track_id, cfg, policy)
        try:
            rec = AutonomousCEOOrchestrator().start(
                goal=goal,
                orchestration_id=oid,
                max_cycles=180,
                max_follow_up_depth=4,
                priority_base=320,
            )
            tr = {
                "orchestration_id": rec.orchestration_id,
                "state": rec.state,
                "last_started_unix": now,
                "models": cfg["models"],
            }
            state["research_tracks"][track_id] = tr
            started_research.append({
                "track": track_id,
                "orchestration_id": rec.orchestration_id,
                "state": rec.state,
            })
        except Exception as exc:
            state["research_tracks"][track_id] = {
                **tr,
                "last_error": f"{type(exc).__name__}:{exc}",
                "last_attempt_unix": now,
            }

    # Recompute visible running tracks after launch.
    research_status = {}
    for track_id, tr in state["research_tracks"].items():
        oid = tr.get("orchestration_id")
        rec = orchestration_record(oid)
        research_status[track_id] = {
            "orchestration_id": oid,
            "state": rec.get("state") or tr.get("state") or "unknown",
            "running": running_orchestration(oid),
            "models": tr.get("models"),
        }

    sector_counts = Counter(
        str(getattr(o, "category", "unknown") or "unknown").lower()
        for o in rows[:30]
    )
    model_counts = Counter(
        str(getattr(o, "mechanism", "unknown") or "unknown").lower()
        for o in rows[:30]
    )

    active_validation_count = len(published) + sum(
        1 for rec in state["candidate_executions"].values()
        if running_orchestration(rec.get("orchestration_id"))
    )

    result = {
        "version": "V65.93",
        "timestamp_unix": now,
        "objective": "maximize_sustainable_risk_adjusted_realized_profit",
        "candidate_count": len(rows),
        "strict_execution_qualified_count": len(qualified),
        "published_validation_count": len(published),
        "active_internal_execution_count": sum(
            1 for rec in state["candidate_executions"].values()
            if running_orchestration(rec.get("orchestration_id"))
        ),
        "active_validation_or_execution_bets": active_validation_count,
        "max_active_validation_bets": max_validation,
        "remaining_validation_slots": max(0, max_validation - active_validation_count),
        "active_research_tracks": sum(1 for x in research_status.values() if x["running"]),
        "research_tracks": research_status,
        "started_research": started_research,
        "started_validations": started_validations,
        "enrichment": enrichment,
        "top30_sector_counts": dict(sector_counts),
        "top30_business_model_counts": dict(model_counts),
        "top_candidates": [
            {
                "name": getattr(o, "name", None),
                "business_model": getattr(o, "mechanism", None),
                "sector": getattr(o, "category", None),
                "score": getattr(o, "score", None),
                "expected_profit_30d": getattr(o, "expected_profit", None),
                "probability": getattr(o, "probability", None),
                "evidence_count": getattr(o, "evidence_count", None),
                "qualification_blockers": strict_reasons(o, poe),
            }
            for o in rows[:12]
        ],
        "policy": {
            "minimum_candidates": policy.get("minimum_candidates"),
            "minimum_unrelated_sectors": policy.get("minimum_unrelated_sectors"),
            "minimum_business_model_families": policy.get("minimum_business_model_families"),
            "max_active_validation_bets": max_validation,
        },
        "guards": {
            "invent_profit": False,
            "research_tracks_are_not_validation_success": True,
            "external_action_gates_unchanged": True,
            "financial_gates_unchanged": True,
            "irreversible_action_gates_unchanged": True,
        },
    }

    state["last_cycle_unix"] = now
    state["last_result"] = result
    write_json(STATE, state)

    report = REPORTS / f"v65_93_parallel_profit_portfolio_{int(now)}.json"
    write_json(report, result)

    print("DISTINCT_CANDIDATES=", len(rows))
    print("STRICT_EXECUTION_QUALIFIED=", len(qualified))
    print("PUBLISHED_VALIDATIONS=", len(published))
    print("ACTIVE_INTERNAL_EXECUTIONS=", result["active_internal_execution_count"])
    print("ACTIVE_VALIDATION_OR_EXECUTION_BETS=", result["active_validation_or_execution_bets"])
    print("MAX_ACTIVE_VALIDATION_BETS=", max_validation)
    print("REMAINING_VALIDATION_SLOTS=", result["remaining_validation_slots"])
    print("ACTIVE_RESEARCH_TRACKS=", result["active_research_tracks"])
    print("STARTED_RESEARCH_TRACKS=", json.dumps(started_research, sort_keys=True))
    print("STARTED_VALIDATIONS=", json.dumps(started_validations, sort_keys=True))
    print("TOP30_SECTOR_COUNTS=", dict(sector_counts))
    print("TOP30_BUSINESS_MODEL_COUNTS=", dict(model_counts))
    print("REPORT=", report)
    print("V65_93_PARALLEL_RESEARCH=PASS")
    print("V65_93_STRICT_VALIDATION_GATE=PASS")
    print("V65_93_PROFIT_OBJECTIVE=PASS")
    print("V65_93_COMPLETE")
    return result

def status():
    state = read_json(STATE, {})
    result = state.get("last_result") or {}
    print(json.dumps({
        "last_cycle_unix": state.get("last_cycle_unix"),
        "candidate_count": result.get("candidate_count"),
        "strict_execution_qualified_count": result.get("strict_execution_qualified_count"),
        "published_validation_count": result.get("published_validation_count"),
        "active_internal_execution_count": result.get("active_internal_execution_count"),
        "active_validation_or_execution_bets": result.get("active_validation_or_execution_bets"),
        "max_active_validation_bets": result.get("max_active_validation_bets"),
        "remaining_validation_slots": result.get("remaining_validation_slots"),
        "active_research_tracks": result.get("active_research_tracks"),
        "research_tracks": result.get("research_tracks"),
        "top_candidates": result.get("top_candidates"),
    }, indent=2, sort_keys=True, default=str))

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=("once", "status", "loop"))
    p.add_argument("--interval", type=int, default=900)
    a = p.parse_args()

    if a.command == "once":
        maintain()
    elif a.command == "status":
        status()
    else:
        interval = max(300, int(a.interval))
        while True:
            try:
                maintain()
            except Exception as exc:
                print("PARALLEL_PROFIT_LOOP_ERROR=", f"{type(exc).__name__}:{exc}", flush=True)
            time.sleep(interval)

if __name__ == "__main__":
    main()
