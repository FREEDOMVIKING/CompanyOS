from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
RUNTIME = ROOT / ".companyos_runtime"
CANDIDATE_DIR = RUNTIME / "profit_first_candidates"
STATE = RUNTIME / "profit_first_enrichment_expansion_state.json"
REPORT = RUNTIME / "profit_first_enrichment_expansion_report.json"
EVIDENCE_REPORT = RUNTIME / "profit_first_evidence_report.json"

TARGET_CANDIDATES = 20
TARGET_SECTORS = 8
TARGET_MODELS = 7
MAX_VALIDATION_BETS = 3

def load(path: Path, default: Any):
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return default

def save(path: Path, obj: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

def current_summary() -> dict[str, Any]:
    er = load(EVIDENCE_REPORT, {})
    ranking = er.get("ranking") or {}
    return {
        "candidate_count": int(er.get("candidate_count", 0) or 0),
        "sector_count": int(er.get("sector_count", 0) or 0),
        "business_model_count": int(er.get("business_model_count", 0) or 0),
        "qualified_count": int(ranking.get("qualified_count", 0) or 0),
        "selected_for_validation": ranking.get("selected_for_validation", []) or [],
        "build_authorized_by_profit_engine": bool(ranking.get("build_authorized_by_profit_engine", False)),
    }

def candidate_files() -> list[Path]:
    if not CANDIDATE_DIR.exists():
        return []
    return sorted(CANDIDATE_DIR.glob("*.json"))

def candidate_snapshot(limit: int = 50) -> list[dict]:
    rows = []
    for p in candidate_files()[:limit]:
        obj = load(p, {})
        if not isinstance(obj, dict):
            continue
        rows.append({
            "name": obj.get("name"),
            "sector": obj.get("sector"),
            "business_model": obj.get("business_model"),
            "evidence_confidence": obj.get("evidence_confidence"),
            "needs_enrichment": obj.get("needs_enrichment"),
            "source": str(p.relative_to(ROOT)),
        })
    return rows

def enrichment_goal() -> str:
    snap = candidate_snapshot()
    return f"""
PROFIT-FIRST EVIDENCE ENRICHMENT MISSION

Current structured candidates:
{json.dumps(snap, indent=2, default=str)}

The current pipeline has candidates, but insufficient evidence quality and/or no qualified opportunities.

For EVERY existing candidate JSON in:
.companyos_runtime/profit_first_candidates/

Do the following:
1. Audit the current scores and identify which values are evidence-backed vs estimated/defaulted.
2. Strengthen market demand evidence.
3. Refine expected revenue, expected profit, margin, recurring revenue, startup costs, capital intensity,
   capital efficiency, and time-to-revenue assumptions.
4. Assess realistic customer acquisition difficulty, plausible channels, competition, differentiation,
   defensibility, scalability, automation potential, probability of success, and regulatory/operational risk.
5. Separate:
   - facts/evidence
   - estimates
   - assumptions
   - unknowns
6. Update evidence_sources with concise source/evidence descriptions.
7. Update evidence_confidence conservatively; never inflate confidence merely to pass a threshold.
8. Keep all numeric scoring fields on a 0-100 scale.
9. Preserve the same canonical candidate identity; do not duplicate or version-bump candidates.
10. Write enriched JSON records back to the same candidate files.
11. Write a summary to:
.companyos_runtime/profit_first_evidence_enrichment_summary.json

This stage is research and analysis only.
Do not perform spending, financial transactions, credential changes, external publication/deployment,
destructive actions, legal commitments, or irreversible actions.
Preserve all existing approval and safety gates.
""".strip()

def expansion_goal() -> str:
    s = current_summary()
    existing = candidate_snapshot()
    return f"""
PROFIT-FIRST OPPORTUNITY EXPANSION MISSION

Current counts:
candidate_count={s['candidate_count']}
sector_count={s['sector_count']}
business_model_count={s['business_model_count']}
qualified_count={s['qualified_count']}

Existing candidates:
{json.dumps(existing, indent=2, default=str)}

The portfolio is not diversified enough.

Expand the opportunity pool until there are AT LEAST:
- {TARGET_CANDIDATES} materially different candidates
- {TARGET_SECTORS} unrelated sectors
- {TARGET_MODELS} business-model families

Actively search across business models such as:
software/SaaS/AI, mobile/web apps, digital products, marketplaces/platforms,
e-commerce/physical products, content/media, data/API/licensing, lead-generation assets,
subscriptions/memberships, automation products, and services.

Rules:
1. Do not generate superficial variants of construction, contractor, bid-organizer, or SMB-AI concepts.
2. Do not count renamed/versioned copies as new opportunities.
3. Prefer commercially distinct opportunities with different customers, economics, channels, and moats.
4. For each new candidate, write one structured JSON record under:
.companyos_runtime/profit_first_candidates/
5. Each record must include:
name, sector, business_model, description,
market_demand, expected_profit, probability_of_success, margin, recurring_revenue,
scalability, capital_efficiency, speed_to_revenue, automation_potential, defensibility,
competition, customer_acquisition_difficulty, regulatory_operational_risk, capital_intensity,
evidence_uncertainty, evidence_confidence, evidence_sources, assumptions, unknowns.
6. Use 0-100 numeric scores.
7. Mark estimates honestly and lower evidence_confidence when evidence is weak.
8. Research/analysis only. Preserve all external-action, financial, credential, signer,
reconciliation, publication/deployment, legal, destructive, and irreversible-action gates.

Write an expansion summary to:
.companyos_runtime/profit_first_opportunity_expansion_summary.json
""".strip()

def validation_goal(selected: list[dict]) -> str:
    return f"""
PROFIT-FIRST VALIDATION QUEUE MISSION

The Profit-First Evidence Engine has selected the following top candidates:
{json.dumps(selected[:MAX_VALIDATION_BETS], indent=2, default=str)}

Create concrete INTERNAL and REVERSIBLE validation work for at most these top {MAX_VALIDATION_BETS} candidates.

For each selected candidate:
- define the highest-risk assumptions
- define the cheapest/fastest validation experiments
- define measurable pass/fail criteria
- define expected cost in internal effort and any external dependency
- define stop/kill conditions
- define evidence required before build authorization
- write a validation plan artifact under:
  .companyos_runtime/profit_first_validation/

Do not auto-build merely because a candidate is selected.
Do not spend money, publish/deploy externally, create legal commitments, change credentials,
or perform irreversible actions without existing approval gates.
""".strip()

def dispatch(goal: str, stage: str, priority: int) -> dict[str, Any]:
    from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
    rec = AutonomousCEOOrchestrator().start(
        goal=goal,
        max_cycles=140,
        max_follow_up_depth=4,
        priority_base=priority,
    )
    return {
        "stage": stage,
        "orchestration_id": getattr(rec, "orchestration_id", None),
        "ts": time.time(),
    }

def maybe_run(cooldown_seconds: int = 300) -> dict[str, Any]:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    st = load(STATE, {"last_run_unix": 0, "runs": []})
    now = time.time()
    since = now - float(st.get("last_run_unix", 0) or 0)
    summary = current_summary()

    if since < cooldown_seconds:
        return {
            "started": False,
            "reason": "cooldown",
            "cooldown_remaining_seconds": round(cooldown_seconds - since, 2),
            "summary": summary,
        }

    if (
        summary["candidate_count"] < TARGET_CANDIDATES
        or summary["sector_count"] < TARGET_SECTORS
        or summary["business_model_count"] < TARGET_MODELS
    ):
        stage = "opportunity_expansion"
        goal = expansion_goal()
        priority = 252
    elif summary["qualified_count"] == 0:
        stage = "evidence_enrichment"
        goal = enrichment_goal()
        priority = 250
    elif summary["selected_for_validation"]:
        stage = "validation_queue"
        goal = validation_goal(summary["selected_for_validation"])
        priority = 248
    else:
        return {"started": False, "reason": "nothing_to_do", "summary": summary}

    try:
        entry = dispatch(goal, stage, priority)
        st["last_run_unix"] = entry["ts"]
        st.setdefault("runs", []).append(entry)
        st["runs"] = st["runs"][-100:]
        save(STATE, st)

        report = {
            "generated_at_unix": entry["ts"],
            "started": True,
            "stage": stage,
            "orchestration_id": entry["orchestration_id"],
            "summary_before": summary,
        }
        save(REPORT, report)
        return report
    except Exception as exc:
        return {
            "started": False,
            "reason": "stage_dispatch_failed",
            "error": f"{type(exc).__name__}: {exc}",
            "summary": summary,
        }
