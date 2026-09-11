from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import json, math, time
from pathlib import Path

ROOT = Path.home() / "companyos"
RUNTIME = ROOT / ".companyos_runtime"
POLICY_PATH = RUNTIME / "profit_first_venture_policy.json"
RANKING_PATH = RUNTIME / "profit_first_venture_rankings.json"

DEFAULT_POLICY = {
  "mission": "Maximize sustainable long-term risk-adjusted economic value by discovering, validating, launching, operating, and scaling the strongest legitimate ventures CompanyOS can execute.",
  "business_model_neutral": True,
  "research_before_build": True,
  "minimum_candidates": 20,
  "minimum_unrelated_sectors": 8,
  "minimum_business_model_families": 7,
  "max_active_validation_bets": 3,
  "minimum_investment_score": 68.0,
  "minimum_evidence_confidence": 0.55,
  "construction_sector_soft_cap": 0.15,
  "service_business_soft_cap": 0.20,
  "no_build_below_threshold": True,
  "portfolio_reallocation_enabled": True,
  "kill_weak_experiments": True,
  "scale_demonstrated_winners": True,
  "external_actions_require_existing_gates": True,
  "financial_transactions_require_existing_gates": True,
  "irreversible_actions_require_existing_gates": True,
  "weights": {
    "expected_profit": 0.20,
    "probability_of_success": 0.14,
    "margin": 0.10,
    "recurring_revenue": 0.08,
    "scalability": 0.10,
    "capital_efficiency": 0.10,
    "speed_to_revenue": 0.07,
    "automation_potential": 0.07,
    "defensibility": 0.05,
    "market_demand": 0.09
  },
  "penalties": {
    "competition": 0.06,
    "customer_acquisition_difficulty": 0.06,
    "regulatory_operational_risk": 0.06,
    "capital_intensity": 0.05,
    "evidence_uncertainty": 0.08
  },
  "required_business_model_families": [
    "software_saas_ai",
    "mobile_web_apps",
    "digital_products",
    "marketplaces_platforms",
    "ecommerce_physical_products",
    "content_media",
    "data_api_licensing",
    "lead_generation_assets",
    "subscriptions_memberships",
    "automation_products",
    "services"
  ]
}

def _clamp(v: Any) -> float:
    try: return max(0.0, min(100.0, float(v)))
    except Exception: return 0.0

def ensure_policy() -> dict:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    if not POLICY_PATH.exists():
        POLICY_PATH.write_text(json.dumps(DEFAULT_POLICY, indent=2) + "\n", encoding="utf-8")
    try:
        p = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except Exception:
        p = DEFAULT_POLICY
    return p

def score_candidate(c: dict, policy: dict | None = None) -> dict:
    policy = policy or ensure_policy()
    w, pen = policy["weights"], policy["penalties"]
    score = 0.0
    for k, weight in w.items():
        score += _clamp(c.get(k, 0)) * float(weight)
    for k, weight in pen.items():
        score -= _clamp(c.get(k, 0)) * float(weight)

    confidence = float(c.get("evidence_confidence", 0) or 0)
    if confidence <= 1: confidence *= 100
    evidence_gate = confidence >= float(policy["minimum_evidence_confidence"]) * 100
    score = max(0.0, min(100.0, score))
    threshold = float(policy["minimum_investment_score"])
    qualified = score >= threshold and evidence_gate

    out = dict(c)
    out.update({
        "profit_first_score": round(score, 3),
        "evidence_gate_passed": evidence_gate,
        "investment_threshold": threshold,
        "qualified_for_validation": qualified,
        "decision": "VALIDATE" if qualified else "RESEARCH_OR_REJECT"
    })
    return out

def rank_candidates(candidates: list[dict]) -> dict:
    policy = ensure_policy()
    ranked = sorted((score_candidate(x, policy) for x in candidates),
                    key=lambda x: x["profit_first_score"], reverse=True)
    qualified = [x for x in ranked if x["qualified_for_validation"]]
    selected = qualified[:int(policy["max_active_validation_bets"])]
    result = {
        "generated_at_unix": time.time(),
        "mission": policy["mission"],
        "candidate_count": len(ranked),
        "qualified_count": len(qualified),
        "selected_for_validation": selected,
        "build_authorized_by_profit_engine": bool(selected),
        "no_build_reason": None if selected else "No evidence-backed opportunity cleared the minimum investment threshold; continue research instead of manufacturing a venture.",
        "ranked_candidates": ranked
    }
    RANKING_PATH.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    return result

def discovery_directive() -> str:
    p = ensure_policy()
    families = ", ".join(p["required_business_model_families"])
    return f"""
COMPANYOS PRIMARY ECONOMIC DIRECTIVE
Mission: {p['mission']}

Do not optimize for number of companies created. Optimize for durable economic value and probability-adjusted profit.

DISCOVERY:
1. Research markets before building.
2. Generate at least {p['minimum_candidates']} materially different opportunities across at least {p['minimum_unrelated_sectors']} unrelated sectors and at least {p['minimum_business_model_families']} business-model families.
3. Business-model families to actively consider: {families}.
4. Construction is allowed but must not dominate merely because prior artifacts exist.
5. Service businesses are allowed but receive no preference over scalable products, software, marketplaces, commerce, media, data, licensing, subscriptions, or automation businesses.
6. Do not clone, rename, version-bump, or superficially mutate existing ventures to satisfy diversity.

EVIDENCE + ECONOMICS:
For every candidate gather or explicitly mark missing evidence for:
- market demand and willingness to pay
- expected revenue and expected profit
- probability of success
- gross/net margin potential
- recurring revenue quality
- scalability
- startup capital and ongoing capital needs
- capital efficiency and expected ROI
- time to first revenue
- automation potential
- competition and differentiation
- defensibility/moat
- customer acquisition difficulty and plausible CAC channels
- regulatory and operational risk
- evidence confidence

DECISION:
Rank candidates by risk-adjusted economic value, not familiarity or ease of artifact generation.
Only the strongest evidence-backed candidates may enter validation.
Maximum simultaneous new validation bets: {p['max_active_validation_bets']}.
Minimum investment score: {p['minimum_investment_score']}/100.
If nothing clears the threshold, CONTINUE RESEARCH. Do not build a mediocre company just to remain busy.

PORTFOLIO:
Compare new opportunities against existing ventures.
Kill or pause weak experiments when evidence deteriorates.
Improve promising ventures.
Reallocate internal attention toward demonstrated winners.
Scale only after measurable evidence supports scaling.
Avoid endless venture creation when improving an existing winner has higher expected value.

EXECUTION:
Internal reversible research, analysis, planning, prototyping, testing, and evidence collection may proceed autonomously through existing CompanyOS capabilities.
Keep consequential external actions, spending, financial transactions, credentials, legal commitments, publication/deployment, destructive actions, and irreversible actions behind all existing approval, authorization, reconciliation, and safety gates.
""".strip()
