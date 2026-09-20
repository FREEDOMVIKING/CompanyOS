"""Pure analytical classifier for identifying the next missing CompanyOS capability."""

from collections import Counter
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

CAPABILITY_ID='capability_gap_classifier'

_REASON_TO_GAP = {
    "missing_external_evidence": "evidence_acquisition",
    "probability_unestimated": "probability_estimation",
    "missing_executable_next_action": "execution_planning",
    "profit_unestimated": "profit_modeling",
    "score_below_execution_threshold": "qualification_tuning",
}

_GAP_METADATA = {
    "evidence_acquisition": {
        "title": "Evidence Acquisition",
        "description": "Collect decision-relevant external evidence before advancing an opportunity.",
        "priority": 5.0,
    },
    "probability_estimation": {
        "title": "Probability Estimation",
        "description": "Estimate execution or realization probability using explicit, inspectable assumptions.",
        "priority": 5.0,
    },
    "execution_planning": {
        "title": "Executable Next-Action Planning",
        "description": "Define a concrete, testable next action for the blocked opportunity.",
        "priority": 5.5,
    },
    "profit_modeling": {
        "title": "Profit Modeling",
        "description": "Make expected realized profit inputs explicit before qualification.",
        "priority": 4.5,
    },
    "qualification_tuning": {
        "title": "Qualification Tuning",
        "description": "Improve qualification inputs or thresholds when opportunities do not meet execution criteria.",
        "priority": 3.5,
    },
    "enrichment_pipeline": {
        "title": "Opportunity Enrichment",
        "description": "Process queued opportunity enrichment work before making a selection.",
        "priority": 2.5,
    },
    "venture_state_observability": {
        "title": "Venture-State Observability",
        "description": "Expose enough structured venture state to identify a defensible next capability.",
        "priority": 1.0,
    },
}


def capability_manifest() -> Dict[str, Any]:
    """Return the static manifest for this analytical capability."""
    return {
        "id": CAPABILITY_ID,
        "title": "Capability Gap Classifier",
        "kind": "safe_analytical",
        "description": "Classifies observed blockers into the next reusable capability gap.",
        "pure": True,
        "side_effects": [],
        "required_inputs": ["context.findings", "context.profit"],
        "output": "ranked capability gaps with observed evidence and limitations",
    }


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _reason_entries(context: Mapping[str, Any]) -> Iterable[Tuple[str, str, Optional[str]]]:
    """Yield (reason, evidence_path, item_id) only for explicit structured reasons."""
    profit = _as_mapping(context.get("profit"))
    rejections = _as_list(profit.get("qualification_rejections"))
    for index, rejection in enumerate(rejections):
        item = _as_mapping(rejection)
        item_id = item.get("id") if isinstance(item.get("id"), str) else None
        for reason in _as_list(item.get("reasons")):
            if isinstance(reason, str) and reason:
                yield reason, "profit.qualification_rejections[%d].reasons" % index, item_id

    for index, finding in enumerate(_as_list(context.get("findings"))):
        item = _as_mapping(finding)
        item_id = item.get("id") if isinstance(item.get("id"), str) else None
        for key in ("reasons", "blockers", "blocking_reasons"):
            for reason in _as_list(item.get(key)):
                if isinstance(reason, str) and reason:
                    yield reason, "findings[%d].%s" % (index, key), item_id


def _evidence_record(reason: str, path: str, item_id: Optional[str]) -> Dict[str, Any]:
    record: Dict[str, Any] = {"reason": reason, "path": path}
    if item_id is not None:
        record["item_id"] = item_id
    return record


def evaluate(context: Mapping[str, Any]) -> Dict[str, Any]:
    """Classify the strongest observed capability gaps without performing side effects."""
    if not isinstance(context, Mapping):
        return {
            "capability_id": CAPABILITY_ID,
            "status": "invalid_input",
            "next_gap": None,
            "ranked_gaps": [],
            "observed_signals": [],
            "limitations": ["context must be a mapping"],
        }

    profit = _as_mapping(context.get("profit"))
    reason_records = list(_reason_entries(context))
    counts = Counter(reason for reason, _, _ in reason_records)
    gap_evidence: Dict[str, List[Dict[str, Any]]] = {}

    for reason, path, item_id in reason_records:
        gap_id = _REASON_TO_GAP.get(reason)
        if gap_id is not None:
            gap_evidence.setdefault(gap_id, []).append(_evidence_record(reason, path, item_id))

    queue_count = profit.get("enrichment_queue_count")
    if isinstance(queue_count, (int, float)) and not isinstance(queue_count, bool) and queue_count > 0:
        gap_evidence.setdefault("enrichment_pipeline", []).append({
            "signal": "enrichment_queue_count",
            "path": "profit.enrichment_queue_count",
            "value": queue_count,
        })

    decision = profit.get("decision")
    if decision == "research_more":
        gap_evidence.setdefault("enrichment_pipeline", []).append({
            "signal": "decision",
            "path": "profit.decision",
            "value": decision,
        })

    ranked: List[Dict[str, Any]] = []
    for gap_id, evidence in gap_evidence.items():
        metadata = _GAP_METADATA[gap_id]
        reason_count = len(evidence)
        score = metadata["priority"] * reason_count
        if gap_id == "enrichment_pipeline" and isinstance(queue_count, (int, float)) and not isinstance(queue_count, bool):
            score += min(float(queue_count), 10.0) * 0.1
        ranked.append({
            "id": gap_id,
            "title": metadata["title"],
            "description": metadata["description"],
            "priority_score": round(score, 3),
            "observed_count": reason_count,
            "evidence": evidence[:10],
        })

    ranked.sort(key=lambda item: (-item["priority_score"], item["id"]))
    limitations = [
        "Scores rank observed blockers; they are not probabilities or financial forecasts.",
        "No missing fact is treated as true unless it is represented by an explicit input signal.",
    ]
    if not ranked:
        limitations.append("No recognized blocker or venture-state signal was provided.")

    next_gap = ranked[0] if ranked else None
    return {
        "capability_id": CAPABILITY_ID,
        "status": "ok",
        "next_gap": next_gap,
        "ranked_gaps": ranked,
        "observed_signals": {
            "reason_counts": dict(sorted(counts.items())),
            "candidate_count": profit.get("candidate_count"),
            "eligible_count": profit.get("eligible_count"),
            "enrichment_queue_count": queue_count,
            "decision": decision,
        },
        "limitations": limitations,
    }
