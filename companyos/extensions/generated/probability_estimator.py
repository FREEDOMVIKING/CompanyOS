CAPABILITY_ID = "probability_estimator"


def capability_manifest():
    return {
        "capability_id": CAPABILITY_ID,
        "title": "Probability Estimator",
        "kind": "analytical",
        "status": "active",
        "safe": True,
        "inputs": ["candidate_records", "semantic_evidence", "scores", "thresholds"],
        "outputs": ["probability_estimates", "planning_guidance", "summary"],
        "side_effects": [],
        "external_actions": False,
        "description": "Produces bounded heuristic qualification probabilities for internal planning only.",
    }


def _number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _clamp(value, lower=0.01, upper=0.99):
    return max(lower, min(upper, value))


def _first_number(record, names):
    for name in names:
        value = _number(record.get(name))
        if value is not None:
            return value
    return None


def _detail_from_context(context):
    if not isinstance(context, dict):
        return {}
    locations = [context]
    compounding = context.get("compounding_request")
    if isinstance(compounding, dict):
        locations.append(compounding)
    for location in locations:
        evidence = location.get("semantic_evidence")
        if isinstance(evidence, dict):
            detail = evidence.get("detail")
            if isinstance(detail, dict):
                return detail
    return {}


def _records_from_context(context):
    records = []
    if not isinstance(context, dict):
        return records
    for key in ("candidates", "candidate_records", "ranked_gaps", "candidate_priority"):
        value = context.get(key)
        if isinstance(value, list):
            records.extend(item for item in value if isinstance(item, dict))
        elif isinstance(value, dict):
            for candidate_id, item in value.items():
                if isinstance(item, dict):
                    record = dict(item)
                    record.setdefault("candidate_id", candidate_id)
                    records.append(record)
    return records


def _estimate(record, fallback_score=None, fallback_gap=None):
    score = _first_number(record, ("score", "candidate_score", "current_score", "average_score"))
    gap = _first_number(record, ("gap", "gap_to_threshold", "shortfall", "average_gap_to_threshold"))
    threshold = _first_number(record, ("threshold", "qualification_threshold", "target", "threshold_score"))
    if score is None:
        score = fallback_score
    if gap is None:
        gap = fallback_gap
    if threshold is None and score is not None and gap is not None:
        threshold = score + gap
    if score is None or threshold is None or threshold <= 0:
        probability = 0.5
        basis = "insufficient_numeric_evidence"
    else:
        probability = _clamp(score / threshold)
        basis = "score_to_threshold_ratio"
    if gap is None and score is not None and threshold is not None:
        gap = max(0.0, threshold - score)
    identifier = record.get("candidate_id", record.get("id", "unknown"))
    if not isinstance(identifier, str):
        identifier = str(identifier)
    if probability < 0.4:
        band = "low"
        guidance = "Prioritize evidence gathering and gap reduction before treating this candidate as likely to qualify."
    elif probability < 0.7:
        band = "moderate"
        guidance = "Treat as uncertain and validate the largest measured gap before allocating additional effort."
    else:
        band = "high"
        guidance = "Candidate is comparatively close to the stated threshold; verify remaining evidence before prioritizing."
    return {
        "candidate_id": identifier,
        "estimated_probability": round(probability, 6),
        "probability_band": band,
        "score": score,
        "threshold": threshold,
        "gap_to_threshold": gap,
        "basis": basis,
        "guidance": guidance,
    }


def evaluate(context):
    if not isinstance(context, dict):
        raise TypeError("context must be a dictionary")
    detail = _detail_from_context(context)
    records = _records_from_context(context)
    fallback_score = _first_number(detail, ("average_score",))
    fallback_gap = _first_number(detail, ("average_gap_to_threshold",))
    if not records:
        candidate_ids = detail.get("candidate_ids")
        if isinstance(candidate_ids, list) and candidate_ids:
            records = [{"candidate_id": item} for item in candidate_ids]
        elif fallback_score is not None or fallback_gap is not None:
            records = [{"candidate_id": "aggregate"}]
    estimates = [_estimate(record, fallback_score, fallback_gap) for record in records]
    probabilities = [item["estimated_probability"] for item in estimates]
    average = round(sum(probabilities) / len(probabilities), 6) if probabilities else None
    low_count = sum(1 for item in estimates if item["probability_band"] == "low")
    moderate_count = sum(1 for item in estimates if item["probability_band"] == "moderate")
    high_count = sum(1 for item in estimates if item["probability_band"] == "high")
    return {
        "capability_id": CAPABILITY_ID,
        "probability_estimates": estimates,
        "planning_guidance": {
            "recommended_sequence": "address_low_probability_gaps_first",
            "next_step": "Validate score and threshold inputs before making resource decisions.",
            "analytical_only": True,
        },
        "summary": {
            "candidate_count": len(estimates),
            "average_estimated_probability": average,
            "low_probability_count": low_count,
            "moderate_probability_count": moderate_count,
            "high_probability_count": high_count,
            "heuristic_warning": "Estimates are bounded score-to-threshold heuristics, not calibrated real-world probabilities.",
        },
    }
