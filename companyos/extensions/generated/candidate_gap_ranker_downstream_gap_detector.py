"""Pure analytical detection of downstream bottlenecks in qualification gaps."""

CAPABILITY_ID = "candidate_gap_ranker_downstream_gap_detector"
_DEFAULT_THRESHOLD = 60.0
_REASON_WEIGHTS = {
    "missing_executable_next_action": 1.5,
    "missing_external_evidence": 1.3,
    "probability_unestimated": 1.2,
    "score_below_execution_threshold": 1.0,
}


def capability_manifest():
    return {
        "id": CAPABILITY_ID,
        "title": "Candidate Gap Ranker Downstream Gap Detector",
        "description": "Aggregates unresolved qualification reasons to identify the most concentrated downstream bottleneck.",
        "kind": "analytical",
        "inputs": [
            "context.candidate_gap_ranker",
            "context.outputs.candidate_gap_ranker",
            "context.profit.qualification_rejections",
        ],
        "outputs": ["bottlenecks", "top_bottleneck", "summary"],
        "safe": True,
        "side_effects": [],
    }


def _mapping(value):
    return value if isinstance(value, dict) else {}


def _candidate_records(context):
    context = _mapping(context)
    candidates = []
    seen = set()

    sources = []
    for key in ("candidate_gap_ranker",):
        value = context.get(key)
        if isinstance(value, dict):
            sources.append(value)
    outputs = context.get("outputs")
    if isinstance(outputs, dict) and isinstance(outputs.get("candidate_gap_ranker"), dict):
        sources.append(outputs["candidate_gap_ranker"])
    profit = context.get("profit")
    if isinstance(profit, dict) and isinstance(profit.get("qualification_rejections"), list):
        sources.append({"qualification_rejections": profit["qualification_rejections"]})

    for source in sources:
        records = source.get("qualification_rejections")
        if not isinstance(records, list):
            records = source.get("ranked_gaps")
        if not isinstance(records, list):
            continue
        for index, raw in enumerate(records):
            record = _mapping(raw)
            reasons = record.get("reasons")
            if isinstance(reasons, str):
                reasons = [reasons]
            if not isinstance(reasons, list):
                reasons = []
            normalized_reasons = []
            for reason in reasons:
                if isinstance(reason, str) and reason.strip():
                    value = reason.strip()
                    if value not in normalized_reasons:
                        normalized_reasons.append(value)
            if not normalized_reasons:
                continue
            candidate_id = record.get("id") or record.get("candidate_id") or record.get("name") or "candidate_" + str(index)
            candidate_id = str(candidate_id)
            identity = (candidate_id, tuple(normalized_reasons))
            if identity in seen:
                continue
            seen.add(identity)
            score = record.get("score")
            try:
                score = float(score)
            except (TypeError, ValueError):
                score = None
            candidates.append({"id": candidate_id, "reasons": normalized_reasons, "score": score})
    return candidates


def evaluate(context):
    """Return deterministic bottleneck observations from supplied runtime context only."""
    context = _mapping(context)
    candidates = _candidate_records(context)
    threshold = context.get("execution_threshold", _DEFAULT_THRESHOLD)
    if isinstance(context.get("profit"), dict):
        threshold = context["profit"].get("execution_threshold", threshold)
    try:
        threshold = float(threshold)
    except (TypeError, ValueError):
        threshold = _DEFAULT_THRESHOLD

    aggregate = {}
    for candidate in candidates:
        for reason in candidate["reasons"]:
            item = aggregate.setdefault(reason, {"ids": [], "scores": []})
            if candidate["id"] not in item["ids"]:
                item["ids"].append(candidate["id"])
            if candidate["score"] is not None:
                item["scores"].append(candidate["score"])

    bottlenecks = []
    for reason, item in aggregate.items():
        count = len(item["ids"])
        scores = item["scores"]
        average_score = round(sum(scores) / len(scores), 2) if scores else None
        average_gap = round(max(0.0, threshold - average_score), 2) if average_score is not None else None
        concentration = count / len(candidates) if candidates else 0.0
        severity = round(count * _REASON_WEIGHTS.get(reason, 1.0) * (1.0 + concentration), 4)
        bottlenecks.append({
            "reason": reason,
            "affected_candidates": count,
            "candidate_ids": sorted(item["ids"]),
            "average_score": average_score,
            "average_gap_to_threshold": average_gap,
            "concentration": round(concentration, 4),
            "severity": severity,
            "unresolved": True,
        })
    bottlenecks.sort(key=lambda item: (-item["severity"], -item["affected_candidates"], item["reason"]))
    top = bottlenecks[0] if bottlenecks else None
    if top:
        summary = "The leading downstream bottleneck is '{}' across {} candidate(s).".format(top["reason"], top["affected_candidates"])
    else:
        summary = "No unresolved downstream bottleneck was observed in the supplied qualification outputs."
    return {
        "capability_id": CAPABILITY_ID,
        "bottlenecks": bottlenecks,
        "top_bottleneck": top,
        "summary": summary,
        "candidate_count": len(candidates),
        "source_observed": bool(candidates),
    }
