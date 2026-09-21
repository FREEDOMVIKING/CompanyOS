from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from companyos.strategy.profit_first_venture_engine import ensure_policy, rank_candidates

ROOT = Path.home() / "companyos"
RUNTIME = Path.home() / ".companyos_runtime"
OUT = RUNTIME / "profit_first_evidence_report.json"

SEARCH_ROOTS = [
    ROOT / "workspace",
    ROOT / "exports",
    ROOT / "artifacts",
    ROOT / ".companyos_runtime",
    RUNTIME,
]

ALIASES = {
    "expected_profit": ["expected_profit", "profit_potential", "profit_score"],
    "probability_of_success": ["probability_of_success", "success_probability", "success_score"],
    "margin": ["margin", "gross_margin", "net_margin", "margin_score"],
    "recurring_revenue": ["recurring_revenue", "recurring_revenue_quality", "rr_score"],
    "scalability": ["scalability", "scale_score"],
    "capital_efficiency": ["capital_efficiency", "roi", "roi_score"],
    "speed_to_revenue": ["speed_to_revenue", "time_to_revenue_score"],
    "automation_potential": ["automation_potential", "automation_score"],
    "defensibility": ["defensibility", "moat", "moat_score"],
    "market_demand": ["market_demand", "demand", "demand_score"],
    "competition": ["competition", "competition_score"],
    "customer_acquisition_difficulty": ["customer_acquisition_difficulty", "cac_difficulty"],
    "regulatory_operational_risk": ["regulatory_operational_risk", "operational_risk", "risk_score"],
    "capital_intensity": ["capital_intensity", "startup_cost_score"],
    "evidence_uncertainty": ["evidence_uncertainty", "uncertainty"],
    "evidence_confidence": ["evidence_confidence", "confidence"],
}

IDENTITY_KEYS = ["name", "title", "venture", "opportunity", "idea", "business_name"]


def _portable_path(path: Path) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)

def _num(v: Any) -> float | None:
    try:
        if isinstance(v, str):
            s = v.strip().replace("%", "")
            if not s:
                return None
            v = float(s)
        v = float(v)
        if 0 <= v <= 1:
            v *= 100
        return max(0.0, min(100.0, v))
    except Exception:
        return None

def _first(d: dict, keys: list[str]):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None

def normalize_candidate(d: dict, source: str) -> dict | None:
    name = _first(d, IDENTITY_KEYS)
    if not name:
        return None

    out = {
        "name": str(name),
        "source": source,
        "sector": d.get("sector") or d.get("industry") or "unknown",
        "business_model": d.get("business_model") or d.get("model") or "unknown",
        "description": d.get("description") or d.get("summary") or "",
    }

    populated = 0
    for target, aliases in ALIASES.items():
        val = _first(d, aliases)
        n = _num(val)
        if n is not None:
            out[target] = n
            populated += 1

    # Only treat it as an evidence-bearing candidate if enough economics are present.
    if populated < 4:
        return None

    if "evidence_confidence" not in out:
        out["evidence_confidence"] = min(90.0, 35.0 + populated * 5.0)

    return out

def _walk(obj: Any, source: str, found: list[dict]):
    if isinstance(obj, dict):
        c = normalize_candidate(obj, source)
        if c:
            found.append(c)
        for v in obj.values():
            _walk(v, source, found)
    elif isinstance(obj, list):
        for v in obj:
            _walk(v, source, found)

def collect_candidates(max_files: int = 1500) -> list[dict]:
    found: list[dict] = []
    seen_files = 0

    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*.json"):
            if seen_files >= max_files:
                break
            seen_files += 1
            try:
                obj = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            _walk(obj, _portable_path(p), found)

    # Deduplicate by normalized name + sector + business model.
    dedup: dict[tuple[str, str, str], dict] = {}
    for c in found:
        key = (
            c["name"].strip().lower(),
            str(c.get("sector", "")).strip().lower(),
            str(c.get("business_model", "")).strip().lower(),
        )
        old = dedup.get(key)
        if old is None or c.get("evidence_confidence", 0) > old.get("evidence_confidence", 0):
            dedup[key] = c

    return list(dedup.values())

def build_evidence_report() -> dict:
    policy = ensure_policy()
    candidates = collect_candidates()

    if candidates:
        ranking = rank_candidates(candidates)
    else:
        ranking = {
            "generated_at_unix": time.time(),
            "mission": policy["mission"],
            "candidate_count": 0,
            "qualified_count": 0,
            "selected_for_validation": [],
            "build_authorized_by_profit_engine": False,
            "no_build_reason": "No evidence-bearing opportunity candidates found yet. Continue market research.",
            "ranked_candidates": [],
        }

    sectors = sorted({str(c.get("sector", "unknown")) for c in candidates})
    models = sorted({str(c.get("business_model", "unknown")) for c in candidates})

    report = {
        "generated_at_unix": time.time(),
        "candidate_count": len(candidates),
        "sector_count": len(sectors),
        "business_model_count": len(models),
        "sectors": sectors,
        "business_models": models,
        "research_requirements_met": {
            "minimum_candidates": len(candidates) >= int(policy["minimum_candidates"]),
            "minimum_unrelated_sectors": len(sectors) >= int(policy["minimum_unrelated_sectors"]),
            "minimum_business_model_families": len(models) >= int(policy["minimum_business_model_families"]),
        },
        "ranking": ranking,
    }

    RUNTIME.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    return report
