"""Pure analytical ranking of candidate execution-qualification gaps."""

from collections import Counter
from typing import Any, Dict, Iterable, List, Mapping, Tuple

CAPABILITY_ID = "candidate_gap_ranker"

_REASON_LABELS = {
    "score_below_execution_threshold": "execution score below threshold",
    "missing_external_evidence": "missing external evidence",
    "probability_unestimated": "probability is unestimated",
    "profit_unestimated": "profit is unestimated",
    "missing_executable_next_action": "missing executable next action",
}

_REASON_WEIGHTS = {
    "missing_executable_next_action": 5.0,
    "missing_external_evidence": 4.0,
    "probability_unestimated": 3.0,
    "profit_unestimated": 3.0,
    "score_below_execution_threshold": 2.0,
}


def capability_manifest() -> dict:
    """Return the stable adapter metadata for this analytical capability."""
    return {
        "id": CAPABILITY_ID,
        "title": "Candidate qualification gap ranker",
        "kind": "analytical",
        "safe": True,
        "side_effects": [],
        "description": (
            "Ranks recurring qualification gaps and candidate remediation order "
            "using only supplied runtime context."
        ),
        "inputs": ["context.profit.qualification_rejections"],
        "outputs": ["ranked_gaps", "candidate_priority", "summary"],
    }


def _as_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _records(context: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    profit = context.get("profit", {}) if isinstance(context, Mapping) else {}
    raw = profit.get("qualification_rejections", []) if isinstance(profit, Mapping) else []
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, Mapping)]


def _normalised_reasons(record: Mapping[str, Any]) -> List[str]:
    raw = record.get("reasons", [])
    if not isinstance(raw, list):
        return []
    return sorted({reason for reason in raw if isinstance(reason, str) and reason})


def _candidate_key(record: Mapping[str, Any], index: int) -> str:
    candidate_id = _as_text(record.get("id"))
    name = _as_text(record.get("name"))
    return candidate_id or name or "candidate_{}".format(index + 1)


def _numeric_score(record: Mapping[str, Any]) -> float:
    value = record.get("score")
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    return score if score == score else 0.0


def evaluate(context: dict) -> dict:
    """Rank gaps without mutating context or performing external operations."""
    records = _records(context)
    gap_data: Dict[str, Dict[str, Any]] = {}
    candidate_priority: List[Dict[str, Any]] = []

    for index, record in enumerate(records):
        key = _candidate_key(record, index)
        reasons = _normalised_reasons(record)
        known_reasons = [reason for reason in reasons if reason in _REASON_LABELS]
        unknown_reasons = [reason for reason in reasons if reason not in _REASON_LABELS]
        for reason in known_reasons:
            item = gap_data.setdefault(
                reason,
                {"reason": reason, "label": _REASON_LABELS[reason], "candidate_count": 0, "candidates": []},
            )
            item["candidate_count"] += 1
            item["candidates"].append(key)
        weighted_gap = sum(_REASON_WEIGHTS.get(reason, 1.0) for reason in reasons)
        candidate_priority.append(
            {
                "id": _as_text(record.get("id")) or None,
                "name": _as_text(record.get("name")) or None,
                "score": _numeric_score(record),
                "gaps": known_reasons,
                "unknown_gaps": unknown_reasons,
                "gap_weight": round(weighted_gap, 2),
                "priority_score": round(weighted_gap * 100.0 + max(0.0, 100.0 - _numeric_score(record)), 2),
                "recommended_focus": _REASON_LABELS[known_reasons[0]] if known_reasons else "validate qualification inputs",
            }
        )

    ranked_gaps = []
    total = len(records)
    for reason, item in gap_data.items():
        prevalence = item["candidate_count"] / total if total else 0.0
        ranked_gaps.append(
            {
                "reason": item["reason"],
                "label": item["label"],
                "candidate_count": item["candidate_count"],
                "prevalence": round(prevalence, 4),
                "priority_weight": _REASON_WEIGHTS.get(reason, 1.0),
                "impact_score": round(prevalence * _REASON_WEIGHTS.get(reason, 1.0) * 100.0, 2),
                "candidates": sorted(item["candidates"]),
            }
        )
    ranked_gaps.sort(key=lambda item: (-item["impact_score"], item["reason"]))
    candidate_priority.sort(key=lambda item: (-item["priority_score"], item["name"] or "", item["id"] or ""))

    return {
        "capability_id": CAPABILITY_ID,
        "summary": {
            "candidate_count": total,
            "ranked_gap_count": len(ranked_gaps),
            "top_gap": ranked_gaps[0]["reason"] if ranked_gaps else None,
            "top_candidate": candidate_priority[0]["id"] if candidate_priority else None,
            "analysis_only": True,
        },
        "ranked_gaps": ranked_gaps,
        "candidate_priority": candidate_priority,
    }
