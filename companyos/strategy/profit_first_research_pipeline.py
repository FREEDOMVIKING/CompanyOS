from __future__ import annotations
import json
import time
from pathlib import Path

ROOT = Path.home() / "companyos"
RUNTIME = Path.home() / ".companyos_runtime"
STATE = RUNTIME / "profit_first_research_pipeline_state.json"
CANDIDATE_DIR = RUNTIME / "profit_first_candidates"

def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

def evidence_summary():
    p = RUNTIME / "profit_first_evidence_report.json"
    r = load(p, {})
    return {
        "candidate_count": int(r.get("candidate_count", 0) or 0),
        "sector_count": int(r.get("sector_count", 0) or 0),
        "business_model_count": int(r.get("business_model_count", 0) or 0),
        "qualified_count": int((r.get("ranking") or {}).get("qualified_count", 0) or 0),
    }

def research_goal():
    from companyos.strategy.profit_first_venture_engine import discovery_directive
    return discovery_directive() + """
RESEARCH PIPELINE OUTPUT CONTRACT

You must produce concrete, structured opportunity evidence files, not only prose.

1. Discover at least 20 materially different opportunities across at least 8 unrelated sectors
   and at least 7 business-model families.
2. For each candidate, create one JSON record under:
   .companyos_runtime/profit_first_candidates/
3. Every candidate JSON must contain:
   name
   sector
   business_model
   description
   market_demand
   expected_profit
   probability_of_success
   margin
   recurring_revenue
   scalability
   capital_efficiency
   speed_to_revenue
   automation_potential
   defensibility
   competition
   customer_acquisition_difficulty
   regulatory_operational_risk
   capital_intensity
   evidence_uncertainty
   evidence_confidence
   evidence_sources
   assumptions
   unknowns
4. Numeric scoring fields must use 0-100.
5. evidence_sources must describe the evidence used; explicitly mark estimates/assumptions.
6. Do not invent certainty. Missing evidence must lower evidence_confidence.
7. Do not duplicate, rename, version-bump, or lightly mutate existing ventures.
8. Construction and service businesses may appear only as part of a genuinely diversified pool.
9. Persist a market-scan summary JSON to:
   .companyos_runtime/profit_first_market_scan_summary.json
10. This stage is research/analysis only. Do not perform spending, financial transactions,
    credential changes, external publication/deployment, destructive actions, legal commitments,
    or irreversible actions. Existing approval and safety gates remain authoritative.
""".strip()

def enrichment_goal():
    return """
PROFIT-FIRST EVIDENCE ENRICHMENT

Review all JSON candidate records in:
.companyos_runtime/profit_first_candidates/

For each candidate:
- identify missing or weak economic evidence
- improve market demand evidence
- refine expected revenue/profit and margin assumptions
- assess competition, customer acquisition difficulty, defensibility, time-to-revenue,
  capital needs, automation potential, scalability, regulatory/operational risk
- explicitly separate facts, estimates, assumptions, and unknowns
- update evidence_confidence conservatively
- preserve 0-100 numeric scoring fields
- do not create duplicate candidates merely to increase candidate count

Persist updated candidate JSON records in place and write:
.companyos_runtime/profit_first_evidence_enrichment_summary.json

Research/analysis only. Preserve all existing approval, financial, external-action,
credential, signer, reconciliation, publication/deployment, legal, destructive,
and irreversible-action gates.
""".strip()

def run_stage(stage):
    from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
    goal = research_goal() if stage == "market_scan" else enrichment_goal()
    rec = AutonomousCEOOrchestrator().start(
        goal=goal,
        max_cycles=140,
        max_follow_up_depth=4,
        priority_base=250 if stage == "market_scan" else 245,
    )
    return getattr(rec, "orchestration_id", None)

def maybe_run(cooldown_seconds=300):
    RUNTIME.mkdir(parents=True, exist_ok=True)
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)

    st = load(STATE, {"last_run_unix": 0, "runs": []})
    summary = evidence_summary()
    since = time.time() - float(st.get("last_run_unix", 0) or 0)

    if since < cooldown_seconds:
        return {"started": False, "reason": "cooldown", "summary": summary}

    if summary["candidate_count"] < 20 or summary["sector_count"] < 8 or summary["business_model_count"] < 7:
        stage = "market_scan"
    elif summary["qualified_count"] == 0:
        stage = "evidence_enrichment"
    else:
        return {"started": False, "reason": "research_sufficient_for_ranking", "summary": summary}

    try:
        oid = run_stage(stage)
        now = time.time()
        entry = {"ts": now, "stage": stage, "orchestration_id": oid}
        st["last_run_unix"] = now
        st.setdefault("runs", []).append(entry)
        st["runs"] = st["runs"][-100:]
        save(STATE, st)
        return {"started": True, "stage": stage, "orchestration_id": oid, "summary": summary}
    except Exception as exc:
        return {
            "started": False,
            "reason": "research_stage_failed",
            "error": f"{type(exc).__name__}: {exc}",
            "summary": summary,
        }
