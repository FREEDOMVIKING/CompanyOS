from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
RT = Path.home() / ".companyos_runtime"
RESEARCH = RT / "canonical_research_outputs"
CANDIDATES = RT / "profit_first_candidates"
STATE = RT / "candidate_enrichment_bridge_state.json"

BAD = (
    "research markets before building",
    "research/analysis only",
    "generate at least",
    "for each candidate",
    "use 0-100 numeric scores",
    "mark estimates honestly",
    "preserve all external",
    "companyos opportunity engine test",
    "this stage is research",
)


def load(path: Path) -> dict[str, Any]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def save(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def _portable_path(path: Path) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def pick(d: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if d.get(key) not in (None, "", [], {}):
            return d[key]
    for nested_key in (
        "candidate",
        "opportunity",
        "business",
        "analysis",
        "market_analysis",
        "economics",
        "scores",
    ):
        nested = d.get(nested_key)
        if isinstance(nested, dict):
            for key in keys:
                if nested.get(key) not in (None, "", [], {}):
                    return nested[key]
    return default


def num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def prob(value: Any) -> float:
    x = num(value, 0)
    if 0 < x <= 1:
        x *= 100
    return max(0.0, min(100.0, x))


def urls(value: Any) -> list[str]:
    out: list[str] = []

    def walk(v: Any) -> None:
        if isinstance(v, dict):
            for z in v.values():
                walk(z)
        elif isinstance(v, list):
            for z in v:
                walk(z)
        elif isinstance(v, str):
            for u in re.findall(r'https?://[^\s"\')\]>]+', v):
                if u not in out:
                    out.append(u)

    walk(value)
    return out[:20]


def semantics(d: dict[str, Any]) -> int:
    keys = {str(k).lower() for k in d}
    wanted = (
        "customer",
        "target_customer",
        "buyer",
        "market",
        "problem",
        "customer_problem",
        "offer",
        "service",
        "product",
        "business_model",
        "revenue_model",
        "mechanism",
    )
    hits = sum(k in keys for k in wanted)
    for nested_key in ("candidate", "opportunity", "business", "market_analysis"):
        nested = d.get(nested_key)
        if isinstance(nested, dict):
            nested_keys = {str(k).lower() for k in nested}
            hits += sum(k in nested_keys for k in wanted)
    return hits


def _monetary_expected_profit(d: dict[str, Any]) -> float:
    schema = str(d.get("schema") or "")
    explicit = pick(
        d,
        "expected_profit_dollars",
        "projected_profit_dollars",
        "expected_net_profit",
        "projected_profit",
        "profit_dollars",
        default=None,
    )
    if explicit not in (None, ""):
        return num(explicit, 0)

    if schema.startswith("companyos.profit_candidate.v69_13"):
        return 0.0

    return num(pick(d, "expected_profit", "profit", default=0), 0)


def normalize(d: dict[str, Any], path: Path) -> dict[str, Any] | None:
    if not isinstance(d, dict) or semantics(d) < 2:
        return None

    text = json.dumps(d, default=str).lower()
    if any(marker in text for marker in BAD) and semantics(d) < 3:
        return None

    name = str(
        pick(
            d,
            "name",
            "opportunity_name",
            "venture_name",
            "business_name",
            "title",
            default=path.stem,
        )
    )[:160]

    evidence = pick(
        d,
        "evidence",
        "evidence_sources",
        "sources",
        "citations",
        "market_evidence",
        default=[],
    )
    source_urls = urls(d)
    evidence_count = (
        len(evidence)
        if isinstance(evidence, (list, dict))
        else (1 if isinstance(evidence, str) and evidence.strip() else 0)
    )
    evidence_count = max(evidence_count, len(source_urls))

    action = str(
        pick(
            d,
            "next_action",
            "recommended_action",
            "execution_action",
            "first_action",
            "recommended_next_step",
            default="",
        )
        or ""
    ).strip()
    if evidence_count < 1 or not action:
        return None

    schema = str(d.get("schema") or "")
    research_profit_score = (
        num(d.get("expected_profit"), 0)
        if schema.startswith("companyos.profit_candidate.v69_13")
        else num(pick(d, "expected_profit_score", "profitability_score", default=0), 0)
    )

    candidate_fingerprint = str(d.get("candidate_fingerprint") or "").strip()
    if not candidate_fingerprint:
        stable = "|".join(
            (
                name.lower(),
                str(pick(d, "business_model", "model", "revenue_model", default="unknown")).lower(),
                str(pick(d, "target_customer", "customer", "buyer", default="unknown")).lower(),
            )
        )
        candidate_fingerprint = hashlib.sha256(stable.encode("utf-8")).hexdigest()[:16]

    return {
        "schema": "companyos.enriched_profit_candidate.v69_15",
        "name": name,
        "business_model": pick(
            d, "business_model", "model", "revenue_model", "mechanism", default="unknown"
        ),
        "target_customer": pick(
            d, "target_customer", "customer", "buyer", "customer_segment", default="unknown"
        ),
        "problem": pick(d, "problem", "customer_problem", "pain_point", default="unknown"),
        "offer": pick(
            d, "offer", "service", "product", "value_proposition", default="unknown"
        ),
        "market": pick(d, "market", "industry", "sector", "category", default="unknown"),
        "expected_profit": _monetary_expected_profit(d),
        "expected_profit_score": research_profit_score,
        "margin": num(
            pick(d, "expected_margin_pct", "margin_pct", "profit_margin", "margin", default=0)
        ),
        "probability": prob(
            pick(
                d,
                "probability_success_pct",
                "probability_of_success",
                "success_probability",
                "probability",
                "confidence",
                default=0,
            )
        ),
        "evidence_count": evidence_count,
        "evidence_quality": prob(
            pick(
                d,
                "evidence_quality_pct",
                "evidence_quality",
                "evidence_confidence",
                default=0,
            )
        ),
        "readiness": prob(
            pick(
                d,
                "execution_readiness_pct",
                "execution_readiness",
                "readiness",
                default=0,
            )
        ),
        "time_to_cash_days": max(
            0.1, num(pick(d, "time_to_cash_days", "days_to_cash", default=30), 30)
        ),
        "capital_required": max(
            0,
            num(
                pick(
                    d,
                    "capital_required",
                    "startup_cost",
                    "required_capital",
                    "cost",
                    default=0,
                )
            ),
        ),
        "next_action": action,
        "evidence": evidence or source_urls,
        "source_urls": source_urls,
        "source_research_artifact": _portable_path(path),
        "candidate_fingerprint": candidate_fingerprint,
        "candidate_origin": d.get("candidate_origin"),
        "hypothesis_only": bool(d.get("hypothesis_only", False)),
        "decision_status": d.get("decision_status"),
        "decision_ready": bool(d.get("decision_ready", False)),
        "execution_ready": bool(d.get("execution_ready", False)),
        "enriched_at_unix": time.time(),
    }


def _source_files(max_age_hours: float) -> list[Path]:
    cutoff = time.time() - max_age_hours * 3600
    found: list[Path] = []
    seen: set[Path] = set()

    for root in (RESEARCH, CANDIDATES):
        if not root.exists():
            continue
        for path in root.rglob("*.json"):
            if path in seen:
                continue
            seen.add(path)
            if path.name.startswith("enriched_"):
                continue
            try:
                if path.stat().st_mtime < cutoff:
                    continue
            except OSError:
                continue
            found.append(path)

    found.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return found


def _stable_output_fingerprint(row: dict[str, Any]) -> str:
    existing = str(row.get("candidate_fingerprint") or "").strip()
    if existing:
        return existing[:24]

    stable = "|".join(
        (
            str(row.get("name") or "").strip().lower(),
            str(row.get("business_model") or "").strip().lower(),
            str(row.get("target_customer") or "").strip().lower(),
            str(row.get("source_research_artifact") or "").strip().lower(),
        )
    )
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()[:16]


def refresh_enrichments(max_age_hours: float = 72) -> dict[str, Any]:
    CANDIDATES.mkdir(parents=True, exist_ok=True)
    scanned = accepted = rejected = 0
    written: list[str] = []
    fingerprints: list[str] = []

    for path in _source_files(max_age_hours):
        scanned += 1
        row = normalize(load(path), path)
        if not row:
            rejected += 1
            continue

        fp = _stable_output_fingerprint(row)
        slug = (
            re.sub(r"[^a-z0-9]+", "_", row["name"].lower()).strip("_")[:72]
            or fp
        )
        out = CANDIDATES / f"enriched_{slug}_{fp}.json"
        save(out, row)
        written.append(_portable_path(out))
        fingerprints.append(fp)
        accepted += 1

        if accepted >= 50:
            break

    state = {
        "schema": "companyos.candidate_enrichment_bridge_state.v69_15",
        "ts": time.time(),
        "scanned": scanned,
        "accepted": accepted,
        "rejected": rejected,
        "written": written,
        "unique_output_fingerprints": len(set(fingerprints)),
        "idempotent_output_names": True,
        "canonical_runtime": str(RT),
    }
    save(STATE, state)
    return state


if __name__ == "__main__":
    print(json.dumps(refresh_enrichments(), indent=2, sort_keys=True))
