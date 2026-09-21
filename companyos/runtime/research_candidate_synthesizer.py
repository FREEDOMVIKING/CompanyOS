from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.request
from pathlib import Path
from typing import Any

from companyos.runtime.public_research_connectors import collect_public_research

ROOT = Path.home() / "companyos"
RUNTIME = Path.home() / ".companyos_runtime"
RAW_DIR = RUNTIME / "canonical_research_outputs"
CANDIDATE_DIR = RUNTIME / "profit_first_candidates"
STATE_PATH = RUNTIME / "research_candidate_synthesizer_state.json"

NUMERIC_FIELDS = (
    "market_demand",
    "expected_profit",
    "probability_of_success",
    "margin",
    "recurring_revenue",
    "scalability",
    "capital_efficiency",
    "speed_to_revenue",
    "automation_potential",
    "defensibility",
    "competition",
    "customer_acquisition_difficulty",
    "regulatory_operational_risk",
    "capital_intensity",
    "evidence_uncertainty",
    "evidence_confidence",
)

DEFAULT_ESTIMATES = {
    "market_demand": 35.0,
    "expected_profit": 30.0,
    "probability_of_success": 20.0,
    "margin": 45.0,
    "recurring_revenue": 35.0,
    "scalability": 50.0,
    "capital_efficiency": 45.0,
    "speed_to_revenue": 35.0,
    "automation_potential": 55.0,
    "defensibility": 25.0,
    "competition": 65.0,
    "customer_acquisition_difficulty": 65.0,
    "regulatory_operational_risk": 35.0,
    "capital_intensity": 45.0,
    "evidence_uncertainty": 80.0,
    "evidence_confidence": 25.0,
}


def _atomic(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def _clamp(value: Any, default: float) -> float:
    try:
        x = float(str(value).replace("%", "").strip())
        if 0 <= x <= 1:
            x *= 100.0
        return round(max(0.0, min(100.0, x)), 3)
    except Exception:
        return float(default)


def _slug(value: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return re.sub(r"_+", "_", s)[:72] or "candidate"


def _fingerprint(candidate: dict[str, Any]) -> str:
    raw = "|".join(
        str(candidate.get(k, "")).strip().lower()
        for k in ("name", "sector", "business_model")
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _safe_source_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    clean = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        url = str(row.get("url") or "").strip()
        source = str(row.get("source") or "public").strip()
        title = str(row.get("title") or "").strip()
        summary = str(row.get("summary") or row.get("content") or "").strip()
        metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        clean.append(
            {
                "source": source,
                "title": title[:500],
                "summary": summary[:4000],
                "url": url[:1500],
                "metadata": metadata,
                "captured_at": row.get("captured_at") or time.time(),
            }
        )
    return clean


def _allowed_urls(rows: list[dict[str, Any]]) -> set[str]:
    return {str(x.get("url") or "").strip() for x in rows if str(x.get("url") or "").strip()}


def _normalize_evidence(value: Any, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    allowed = _allowed_urls(rows)
    out: list[dict[str, Any]] = []

    values = value if isinstance(value, list) else [value] if value else []
    for item in values:
        if isinstance(item, dict):
            url = str(item.get("url") or item.get("link") or "").strip()
            if url and url in allowed:
                out.append(
                    {
                        "source": str(item.get("source") or item.get("publisher") or "public"),
                        "title": str(item.get("title") or "")[:500],
                        "url": url,
                        "claim": str(item.get("claim") or item.get("note") or "")[:2000],
                    }
                )
        elif isinstance(item, str):
            urls = re.findall(r"https?://[^\s\"')\]>]+", item)
            for url in urls:
                if url in allowed:
                    out.append({"source": "public", "url": url, "claim": item[:2000]})

    seen = set()
    dedup = []
    for item in out:
        key = item.get("url")
        if key and key not in seen:
            seen.add(key)
            dedup.append(item)

    if not dedup:
        for row in rows[:3]:
            if row.get("url"):
                dedup.append(
                    {
                        "source": row.get("source") or "public",
                        "title": row.get("title") or "",
                        "url": row.get("url"),
                        "claim": "Observed public research signal used only as hypothesis evidence.",
                    }
                )
    return dedup[:10]


def normalize_candidate(
    candidate: dict[str, Any],
    *,
    topic: str,
    source_rows: list[dict[str, Any]],
    subject: str,
    origin: str,
) -> dict[str, Any] | None:
    if not isinstance(candidate, dict):
        return None

    name = str(candidate.get("name") or candidate.get("title") or "").strip()
    description = str(
        candidate.get("description")
        or candidate.get("summary")
        or candidate.get("thesis")
        or ""
    ).strip()
    sector = str(
        candidate.get("sector")
        or candidate.get("market")
        or candidate.get("industry")
        or topic
        or "unknown"
    ).strip()
    business_model = str(
        candidate.get("business_model")
        or candidate.get("revenue_model")
        or candidate.get("model")
        or "software_or_service_hypothesis"
    ).strip()

    if not name or not description:
        return None

    out: dict[str, Any] = {
        "schema": "companyos.profit_candidate.v69_13",
        "name": name[:180],
        "sector": sector[:120],
        "business_model": business_model[:160],
        "description": description[:5000],
        "target_customer": str(candidate.get("target_customer") or candidate.get("customer") or "unknown")[:300],
        "problem": str(candidate.get("problem") or candidate.get("customer_problem") or "unknown")[:1000],
        "offer": str(candidate.get("offer") or candidate.get("product") or candidate.get("service") or "unknown")[:1000],
        "next_action": str(
            candidate.get("next_action")
            or "Collect direct buyer-demand and pricing evidence before guarded execution."
        )[:1000],
        "research_subject": subject[:3000],
        "research_topic": topic[:500],
        "candidate_origin": origin,
        "hypothesis_only": True,
        "decision_status": "research_required",
        "execution_ready": False,
        "readiness": 0.0,
        "materialized_at_unix": time.time(),
    }

    estimated = []
    for field in NUMERIC_FIELDS:
        default = DEFAULT_ESTIMATES[field]
        if field in candidate:
            out[field] = _clamp(candidate.get(field), default)
        else:
            out[field] = default
            estimated.append(field)

    evidence = _normalize_evidence(
        candidate.get("evidence_sources")
        or candidate.get("sources")
        or candidate.get("evidence"),
        source_rows,
    )
    out["evidence_sources"] = evidence
    out["evidence_count"] = len(evidence)
    out["source_urls"] = [x["url"] for x in evidence if x.get("url")]
    out["assumptions"] = candidate.get("assumptions") or []
    out["unknowns"] = candidate.get("unknowns") or []
    out["estimated_fields"] = estimated

    if not evidence:
        out["evidence_confidence"] = min(out["evidence_confidence"], 10.0)
        out["evidence_uncertainty"] = max(out["evidence_uncertainty"], 90.0)

    out["score"] = min(
        55.0,
        round(
            0.28 * out["market_demand"]
            + 0.22 * out["expected_profit"]
            + 0.18 * out["probability_of_success"]
            + 0.12 * out["capital_efficiency"]
            + 0.10 * out["speed_to_revenue"]
            + 0.10 * out["automation_potential"],
            3,
        ),
    )
    out["candidate_fingerprint"] = _fingerprint(out)
    return out


def _engagement_score(row: dict[str, Any]) -> float:
    meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    vals = []
    for key in ("points", "comments", "stars", "forks", "score", "answers", "views"):
        try:
            x = float(meta.get(key) or 0)
        except Exception:
            x = 0.0
        if x > 0:
            vals.append(x)
    if not vals:
        return 35.0
    raw = max(vals)
    return round(min(65.0, 30.0 + (raw ** 0.5) * 2.2), 3)


def fallback_candidates(
    *,
    subject: str,
    topic: str,
    source_rows: list[dict[str, Any]],
    max_candidates: int = 4,
) -> list[dict[str, Any]]:
    # Grounded fallback when the reasoning service is unavailable. These are
    # explicitly low-confidence hypotheses and are never execution-ready.
    out = []
    for row in source_rows[: max(1, int(max_candidates))]:
        title = str(row.get("title") or "").strip()
        if not title:
            continue
        demand = _engagement_score(row)
        raw = {
            "name": f"Commercialization hypothesis: {title}"[:180],
            "sector": topic or "public_market_signal",
            "business_model": "software_or_service_hypothesis",
            "description": (
                "Investigate whether the observed public signal represents a repeatable "
                "customer problem that can support a paid software, data, automation, "
                "information, or service offer. This is a hypothesis, not validated demand."
            ),
            "target_customer": "unknown",
            "problem": title,
            "offer": "unknown_until_buyer_research",
            "market_demand": demand,
            "expected_profit": 30,
            "probability_of_success": 20,
            "margin": 45,
            "recurring_revenue": 35,
            "scalability": 50,
            "capital_efficiency": 45,
            "speed_to_revenue": 35,
            "automation_potential": 55,
            "defensibility": 25,
            "competition": 65,
            "customer_acquisition_difficulty": 65,
            "regulatory_operational_risk": 35,
            "capital_intensity": 45,
            "evidence_uncertainty": 82,
            "evidence_confidence": 25,
            "evidence_sources": [
                {
                    "source": row.get("source") or "public",
                    "title": title,
                    "url": row.get("url") or "",
                    "claim": row.get("summary") or "Observed public research signal.",
                }
            ],
            "assumptions": [
                "The observed signal may correspond to a commercially relevant problem.",
                "Monetization, buyer identity, pricing, and willingness-to-pay are not yet validated.",
            ],
            "unknowns": [
                "buyer willingness to pay",
                "market size",
                "competitive intensity",
                "unit economics",
                "distribution channel",
            ],
        }
        c = normalize_candidate(
            raw,
            topic=topic,
            source_rows=source_rows,
            subject=subject,
            origin="public_signal_grounded_fallback",
        )
        if c:
            out.append(c)
    return out


def _extract_json_text(content: str) -> Any:
    text = (content or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError("reasoner_output_not_json")


def _reasoner_candidates(
    *,
    subject: str,
    topic: str,
    source_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str | None]:
    url = os.getenv("COMPANYOS_REASONING_URL", "http://127.0.0.1:8765/reason")
    timeout = max(10, min(90, int(os.getenv("COMPANYOS_RESEARCH_REASONING_TIMEOUT_SECONDS", "45"))))

    system = '''
You are the CompanyOS profit-first research synthesizer.
Use ONLY the supplied public research rows as external evidence.
Do not invent URLs, buyers, revenue, prices, market sizes, quotes, or certainty.
Generate commercially distinct OPPORTUNITY HYPOTHESES, not summaries of articles.
Return JSON only with this shape:
{"candidates":[{...}]}

Each candidate must contain:
name, sector, business_model, description, target_customer, problem, offer, next_action,
market_demand, expected_profit, probability_of_success, margin, recurring_revenue,
scalability, capital_efficiency, speed_to_revenue, automation_potential, defensibility,
competition, customer_acquisition_difficulty, regulatory_operational_risk,
capital_intensity, evidence_uncertainty, evidence_confidence,
evidence_sources, assumptions, unknowns.

All score fields are 0-100. evidence_sources must use only URLs supplied in the input.
Low evidence must produce low confidence and high uncertainty.
Do not mark anything execution-ready. Research only.
'''.strip()

    task = {
        "research_subject": subject,
        "rotating_public_topic": topic,
        "source_rows": source_rows[:12],
        "maximum_candidates": 6,
    }
    payload = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(task, default=str)},
        ]
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
    except Exception as exc:
        return [], f"{type(exc).__name__}:{exc}"

    if not data.get("success"):
        return [], f"reasoner_unsuccessful:{data.get('error') or data.get('message') or 'unknown'}"

    provider = data.get("provider_response") if isinstance(data.get("provider_response"), dict) else {}
    choices = provider.get("choices") if isinstance(provider.get("choices"), list) else []
    content = None
    if choices:
        content = ((choices[0] or {}).get("message") or {}).get("content")
    if not content:
        return [], "reasoner_content_missing"

    try:
        obj = _extract_json_text(content)
    except Exception as exc:
        return [], f"{type(exc).__name__}:{exc}"

    rows = obj.get("candidates") if isinstance(obj, dict) else None
    if not isinstance(rows, list):
        return [], "reasoner_candidates_missing"

    normalized = []
    for item in rows[:8]:
        c = normalize_candidate(
            item,
            topic=topic,
            source_rows=source_rows,
            subject=subject,
            origin="public_signal_grounded_reasoning",
        )
        if c:
            normalized.append(c)
    return normalized, None


def _persist_candidate(candidate: dict[str, Any]) -> str:
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    fp = candidate["candidate_fingerprint"]
    path = CANDIDATE_DIR / f"{_slug(candidate['name'])}_{fp}.json"
    existing = {}
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        existing = {}
    if existing:
        old_conf = _clamp(existing.get("evidence_confidence"), 0)
        new_conf = _clamp(candidate.get("evidence_confidence"), 0)
        if old_conf > new_conf:
            return str(path)
    _atomic(path, candidate)
    return str(path)


def run_for_task(subject: str, supplied_evidence: Any = None) -> dict[str, Any]:
    started = time.time()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)

    topic = ""
    public_rows: list[dict[str, Any]] = []
    public_errors: list[str] = []
    try:
        topic, public_rows, public_errors = collect_public_research()
    except Exception as exc:
        public_errors = [f"collect_public_research:{type(exc).__name__}:{exc}"]

    rows = _safe_source_rows(public_rows)

    if isinstance(supplied_evidence, list):
        supplied_rows = [x for x in supplied_evidence if isinstance(x, dict)]
        rows.extend(_safe_source_rows(supplied_rows))

    raw_bundle = {
        "schema": "companyos.canonical_research_bundle.v69_13",
        "research_subject": subject,
        "public_topic": topic,
        "source_rows": rows,
        "public_errors": public_errors,
        "external_research_performed": bool(public_rows),
        "captured_at_unix": time.time(),
    }
    raw_fp = hashlib.sha256(
        (subject + "|" + topic + "|" + json.dumps(rows, sort_keys=True, default=str)).encode("utf-8")
    ).hexdigest()[:18]
    raw_path = RAW_DIR / f"research_bundle_{int(started*1000)}_{raw_fp}.json"
    _atomic(raw_path, raw_bundle)

    reasoned, reasoner_error = ([], "no_source_rows")
    if rows:
        reasoned, reasoner_error = _reasoner_candidates(
            subject=subject,
            topic=topic,
            source_rows=rows,
        )

    candidates = reasoned
    mode = "grounded_reasoning"
    if not candidates and rows:
        candidates = fallback_candidates(
            subject=subject,
            topic=topic,
            source_rows=rows,
            max_candidates=4,
        )
        mode = "grounded_fallback"

    written = [_persist_candidate(c) for c in candidates]
    result = {
        "schema": "companyos.research_candidate_synthesis_result.v69_13",
        "started_at_unix": started,
        "finished_at_unix": time.time(),
        "subject": subject,
        "topic": topic,
        "source_count": len(rows),
        "public_source_count": len(public_rows),
        "external_research_performed": bool(public_rows),
        "public_errors": public_errors,
        "reasoner_error": reasoner_error,
        "synthesis_mode": mode if candidates else "no_candidates",
        "candidate_count": len(candidates),
        "candidate_files": written,
        "raw_research_artifact": str(raw_path),
        "execution_ready_candidates_created": 0,
        "financial_actions_performed": False,
        "external_actions_performed": False,
    }
    _atomic(STATE_PATH, result)
    return result


def status() -> dict[str, Any]:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"status": "not_run", "runtime": str(RUNTIME)}


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("command", nargs="?", default="status", choices=("status", "once"))
    ap.add_argument("--subject", default="Discover evidence-grounded profitable opportunities")
    args = ap.parse_args()
    if args.command == "once":
        print(json.dumps(run_for_task(args.subject), indent=2, sort_keys=True, default=str))
    else:
        print(json.dumps(status(), indent=2, sort_keys=True, default=str))
