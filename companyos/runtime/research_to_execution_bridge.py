from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
RT = Path.home() / ".companyos_runtime"
CANDIDATES = RT / "profit_first_candidates"
STATE = RT / "research_to_execution_bridge.json"

POLICY_WORDS = {
    "do_not", "must_", "research_analysis_only", "evidence_sources",
    "numeric_scoring", "mark_estimates", "missing_evidence",
    "duplicate_rename", "candidate_files_written", "generate_at_least",
    "construction_is_allowed", "this_stage_is_research",
    "persist_a_market_scan", "every_candidate_json",
    "companyos_opportunity_engine_test", "one_shot_token",
}

IMPERATIVE_NAME_PATTERNS = (
    "prefer ",
    "for each ",
    "use 0-100",
    "use 0_100",
    "research markets",
    "discover at least",
    "generate at least",
    "do not ",
    "must ",
    "every candidate",
    "construction and service businesses may",
    "persist a market scan",
    "this stage is research",
    "mark estimates",
    "evidence sources",
)

SEMANTIC_KEYS = (
    "business_model",
    "target_customer",
    "customer_segment",
    "customer_problem",
    "problem",
    "offer",
    "product",
    "service",
    "value_proposition",
    "pricing",
    "price",
    "revenue_model",
    "market",
)

NAME_KEYS = (
    "name", "candidate_name", "venture_name", "business_name",
    "title", "opportunity", "idea", "concept",
)
MODEL_KEYS = (
    "business_model", "model", "offer", "product", "service",
    "value_proposition", "customer_problem", "target_customer",
)
SCORE_KEYS = (
    "score", "composite_score", "total_score", "opportunity_score",
    "profitability_score", "expected_value_score", "rank_score",
)


@dataclass
class Candidate:
    source: str
    fingerprint: str
    slug: str
    name: str
    score: float
    payload: dict[str, Any]
    confidence: float
    evidence_count: int


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return re.sub(r"_+", "_", value)[:72]


def _text(obj: Any) -> str:
    try:
        return json.dumps(obj, sort_keys=True, default=str).lower()
    except Exception:
        return str(obj).lower()


def _name(payload: dict[str, Any], source: Path) -> str:
    for key in NAME_KEYS:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()[:140]
    return source.stem.replace("_", " ")[:140]


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        x = float(value)
        if 0 <= x <= 1:
            return x * 100.0
        return max(0.0, min(100.0, x))
    try:
        x = float(str(value).strip())
        if 0 <= x <= 1:
            x *= 100.0
        return max(0.0, min(100.0, x))
    except Exception:
        return None


def _score(payload: dict[str, Any]) -> float:
    vals = []
    for key in SCORE_KEYS:
        if key in payload:
            n = _numeric(payload.get(key))
            if n is not None:
                vals.append(n)

    scores = payload.get("scores")
    if isinstance(scores, dict):
        for value in scores.values():
            n = _numeric(value)
            if n is not None:
                vals.append(n)

    if vals:
        return round(sum(vals) / len(vals), 2)

    heuristic = 0.0
    text = _text(payload)
    if any(k in payload for k in MODEL_KEYS):
        heuristic += 30
    if any(x in text for x in ("customer", "market", "demand", "buyer")):
        heuristic += 15
    if any(x in text for x in ("revenue", "price", "margin", "profit")):
        heuristic += 15
    if any(x in text for x in ("evidence", "source", "competitor")):
        heuristic += 15
    if len(text) > 500:
        heuristic += 10
    return min(100.0, heuristic)


def _confidence(payload: dict[str, Any]) -> float:
    for key in ("confidence", "evidence_confidence", "confidence_score"):
        if key in payload:
            n = _numeric(payload.get(key))
            if n is not None:
                return n
    return 50.0


def _evidence_count(payload: dict[str, Any]) -> int:
    count = 0
    for key in ("evidence", "sources", "citations", "market_evidence"):
        value = payload.get(key)
        if isinstance(value, list):
            count += len(value)
        elif isinstance(value, dict):
            count += len(value)
        elif isinstance(value, str) and value.strip():
            count += 1
    return count


def _looks_like_policy(source: Path, payload: dict[str, Any]) -> bool:
    stem = source.stem.lower()
    if any(word in stem for word in POLICY_WORDS):
        return True

    name = _name(payload, source).strip().lower()
    if any(name.startswith(x) or x in name for x in IMPERATIVE_NAME_PATTERNS):
        return True

    keys = {str(k).lower() for k in payload}
    text = _text(payload)

    instruction_markers = (
        "must not",
        "do not perform",
        "research only",
        "candidate json must",
        "generate at least",
        "this stage is research",
        "scoring fields must",
        "for each candidate",
        "prefer commercially distinct",
        "use 0-100 numeric scores",
        "research markets before building",
    )
    if any(x in text for x in instruction_markers):
        semantic_hits = sum(1 for k in SEMANTIC_KEYS if k in keys)
        if semantic_hits < 2:
            return True

    return False


def _semantic_candidate_strength(payload: dict[str, Any]) -> int:
    keys = {str(k).lower() for k in payload}
    hits = sum(1 for k in SEMANTIC_KEYS if k in keys)

    # Nested business records are also acceptable.
    for nested_key in ("candidate", "business", "opportunity_details", "market_analysis"):
        nested = payload.get(nested_key)
        if isinstance(nested, dict):
            nested_keys = {str(k).lower() for k in nested}
            hits += sum(1 for k in SEMANTIC_KEYS if k in nested_keys)

    return hits


def _has_explicit_score(payload: dict[str, Any]) -> bool:
    if any(k in payload for k in SCORE_KEYS):
        return True
    scores = payload.get("scores")
    return isinstance(scores, dict) and any(_numeric(v) is not None for v in scores.values())


def _promotion_quality(candidate: Candidate) -> tuple[bool, list[str]]:
    reasons = []
    if candidate.score < 60:
        reasons.append("score_below_60")
    if candidate.confidence < 35 and candidate.evidence_count < 1:
        reasons.append("insufficient_confidence_and_evidence")
    if _semantic_candidate_strength(candidate.payload) < 2:
        reasons.append("insufficient_business_semantics")
    if not _has_explicit_score(candidate.payload):
        reasons.append("no_explicit_candidate_score")
    return (not reasons), reasons


def scan_candidates(min_score: float = 45.0) -> list[Candidate]:
    if not CANDIDATES.exists():
        return []

    found: dict[str, Candidate] = {}
    for path in CANDIDATES.glob("*.json"):
        payload = _load(path, {})
        if not isinstance(payload, dict) or not payload:
            continue
        if _looks_like_policy(path, payload):
            continue

        name = _name(payload, path)
        slug = _slug(name)
        if not slug or len(slug) < 3:
            continue

        # A real opportunity must look like a business candidate, not a rule,
        # instruction, test artifact, or generic research directive.
        if _semantic_candidate_strength(payload) < 2:
            continue
        if not _has_explicit_score(payload):
            continue

        score = _score(payload)
        if score < min_score:
            continue

        raw = json.dumps(payload, sort_keys=True, default=str)
        fp = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]
        candidate = Candidate(
            source=str(path.relative_to(ROOT)),
            fingerprint=fp,
            slug=slug,
            name=name,
            score=score,
            payload=payload,
            confidence=_confidence(payload),
            evidence_count=_evidence_count(payload),
        )
        old = found.get(slug)
        if old is None or candidate.score > old.score:
            found[slug] = candidate

    return sorted(
        found.values(),
        key=lambda c: (c.score, c.confidence, c.evidence_count),
        reverse=True,
    )


def _state():
    state = _load(STATE, {})
    if not isinstance(state, dict):
        state = {}
    state.setdefault("promotions", [])
    state.setdefault("promoted_fingerprints", {})
    state.setdefault("last_promotion_unix", 0)
    return state


def _workspace_exists(slug: str) -> bool:
    return any(
        (ROOT / base / slug).exists()
        for base in ("workspace", "products", "artifacts", "exports")
    )


def _write_venture(candidate: Candidate) -> Path:
    venture = ROOT / "workspace" / candidate.slug
    venture.mkdir(parents=True, exist_ok=True)

    brief = {
        "canonical_id": candidate.slug,
        "name": candidate.name,
        "stage": "VALIDATE",
        "source_candidate": candidate.source,
        "candidate_fingerprint": candidate.fingerprint,
        "candidate_score": candidate.score,
        "candidate_confidence": candidate.confidence,
        "evidence_count": candidate.evidence_count,
        "candidate": candidate.payload,
        "promoted_at_unix": time.time(),
        "next_required_outcome": (
            "Produce one measurable validation artifact and, if validation "
            "passes, build the smallest sellable product or service."
        ),
    }
    _save(venture / "venture_brief.json", brief)
    _save(
        venture / "venture_stage_VALIDATE.json",
        {
            "stage": "VALIDATE",
            "updated_at_unix": time.time(),
            "source": "research_to_execution_bridge",
        },
    )
    return venture


def _execution_goal(candidate: Candidate) -> str:
    return f'''
Advance canonical CompanyOS venture '{candidate.slug}' from RESEARCH into EXECUTION.

Candidate: {candidate.name}
Research score: {candidate.score}
Confidence: {candidate.confidence}
Evidence count: {candidate.evidence_count}
Source artifact: {candidate.source}

EXECUTION CONTRACT:
1. Reuse the existing promoted venture workspace. Do not create renamed/versioned clones.
2. Validate one concrete customer problem, buyer, offer, price hypothesis, and measurable success criterion.
3. If validation is adequate, build the smallest sellable product/service artifact.
4. Run acceptance tests and fix only failures required to pass.
5. Package a launch candidate and prepare customer-facing assets.
6. If existing CompanyOS policy and configured connector gates authorize the action, advance through deployment and measurable customer acquisition. Never bypass an approval/safety gate.
7. Record stage changes and measurable evidence in the venture workspace.
8. Do not return to broad market research unless validation produces a specific evidence gap.
9. Do not perform a financial transaction merely to prove activity. Financial actions must remain within the existing live-finance policy, signer, reconciliation, and transaction-limit controls.

The required outcome is measurable venture progression, not another market scan.
'''.strip()


def promote(candidate: Candidate) -> dict[str, Any]:
    venture = _write_venture(candidate)

    from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator

    rec = AutonomousCEOOrchestrator().start(
        goal=_execution_goal(candidate),
        max_cycles=180,
        max_follow_up_depth=7,
        priority_base=320,
    )
    oid = getattr(rec, "orchestration_id", None)

    state = _state()
    entry = {
        "ts": time.time(),
        "canonical_id": candidate.slug,
        "name": candidate.name,
        "score": candidate.score,
        "confidence": candidate.confidence,
        "source": candidate.source,
        "fingerprint": candidate.fingerprint,
        "workspace": str(venture.relative_to(ROOT)),
        "orchestration_id": oid,
    }
    state["promotions"].append(entry)
    state["promotions"] = state["promotions"][-200:]
    state["promoted_fingerprints"][candidate.fingerprint] = entry["ts"]
    state["last_promotion_unix"] = entry["ts"]
    _save(STATE, state)
    return {"started": True, "entry": entry}


def maybe_promote_candidate(
    min_score: float = 45.0,
    cooldown_seconds: int = 900,
    max_existing_execution_ventures: int = 3,
) -> dict[str, Any]:
    candidates = scan_candidates(min_score=min_score)
    state = _state()
    now = time.time()

    execution_ventures = 0
    for base in ("workspace", "products", "exports"):
        root = ROOT / base
        if root.exists():
            execution_ventures += sum(1 for x in root.iterdir() if x.is_dir())

    eligible = []
    rejected = []
    for c in candidates:
        if c.fingerprint in state["promoted_fingerprints"]:
            continue
        if _workspace_exists(c.slug):
            continue
        ok, reasons = _promotion_quality(c)
        if not ok:
            rejected.append({
                "name": c.name,
                "slug": c.slug,
                "score": c.score,
                "confidence": c.confidence,
                "evidence_count": c.evidence_count,
                "reasons": reasons,
            })
            continue
        eligible.append(c)

    detail = {
        "candidate_count": len(candidates),
        "eligible_count": len(eligible),
        "execution_venture_count": execution_ventures,
        "rejected_count": len(rejected),
        "rejected_candidates": rejected[:10],
        "top_candidates": [
            {
                "name": c.name,
                "slug": c.slug,
                "score": c.score,
                "confidence": c.confidence,
                "evidence_count": c.evidence_count,
            }
            for c in candidates[:5]
        ],
    }

    if not eligible:
        return {"started": False, "reason": "no_unpromoted_eligible_candidate", **detail}

    if execution_ventures >= max_existing_execution_ventures:
        return {"started": False, "reason": "execution_capacity_full", **detail}

    since_last = now - float(state.get("last_promotion_unix", 0) or 0)
    if since_last < cooldown_seconds:
        return {
            "started": False,
            "reason": "promotion_cooldown",
            "seconds_remaining": round(cooldown_seconds - since_last, 1),
            **detail,
        }

    try:
        return {**promote(eligible[0]), **detail}
    except Exception as exc:
        return {
            "started": False,
            "reason": "promotion_failed",
            "error": f"{type(exc).__name__}:{exc}",
            **detail,
        }


def status() -> dict[str, Any]:
    candidates = scan_candidates()
    state = _state()
    top = []
    for c in candidates[:10]:
        row = asdict(c)
        row["payload"] = None
        top.append(row)
    return {
        "candidate_count": len(candidates),
        "top_candidates": top,
        "promotion_count": len(state["promotions"]),
        "recent_promotions": state["promotions"][-10:],
        "last_promotion_unix": state.get("last_promotion_unix", 0),
    }
