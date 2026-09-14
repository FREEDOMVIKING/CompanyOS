"""Deterministic analytical guidance for execution readiness findings."""

CAPABILITY_ID = "execution_readiness_improver"
SOURCE_CAPABILITY = "candidate_gap_ranker_downstream_gap_detector"
DEFAULT_EXECUTION_THRESHOLD = 60.0


def capability_manifest():
    """Return the static manifest for this safe analytical capability."""
    return {
        "capability_id": CAPABILITY_ID,
        "title": "Execution Readiness Improver",
        "kind": "analytical",
        "safe": True,
        "side_effects": [],
        "source_capability": SOURCE_CAPABILITY,
        "inputs": [
            "compounding_request.semantic_evidence.detail",
            "compounding_request.priority",
        ],
        "outputs": [
            "readiness_assessment",
            "planning_guidance",
            "evidence_summary",
        ],
        "execution_allowed": False,
        "external_action_allowed": False,
    }


def _number(value, default):
    """Return a finite numeric value, otherwise the supplied default."""
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        if value == value and value not in (float("inf"), float("-inf")):
            return float(value)
    return default


def _detail(context):
    if not isinstance(context, dict):
        return {}
    request = context.get("compounding_request", {})
    if not isinstance(request, dict):
        return {}
    evidence = request.get("semantic_evidence", {})
    if not isinstance(evidence, dict):
        return {}
    detail = evidence.get("detail", {})
    return detail if isinstance(detail, dict) else {}


def evaluate(context):
    """Evaluate readiness evidence and return internal planning guidance only."""
    detail = _detail(context)
    request = context.get("compounding_request", {}) if isinstance(context, dict) else {}
    if not isinstance(request, dict):
        request = {}

    raw_ids = detail.get("candidate_ids", [])
    candidate_ids = []
    if isinstance(raw_ids, list):
        for candidate_id in raw_ids:
            if isinstance(candidate_id, str) and candidate_id and candidate_id not in candidate_ids:
                candidate_ids.append(candidate_id)

    affected = detail.get("affected_candidates", len(candidate_ids))
    affected = max(0, int(_number(affected, len(candidate_ids))))
    threshold = _number(
        detail.get("execution_threshold", request.get("execution_threshold", DEFAULT_EXECUTION_THRESHOLD)),
        DEFAULT_EXECUTION_THRESHOLD,
    )
    if threshold < 0:
        threshold = DEFAULT_EXECUTION_THRESHOLD
    average_score = _number(detail.get("average_score"), 0.0)
    supplied_gap = detail.get("average_gap_to_threshold")
    gap = _number(supplied_gap, max(0.0, threshold - average_score))
    gap = max(0.0, gap)
    score_percent = round(max(0.0, min(100.0, (average_score / threshold * 100.0) if threshold else 100.0)), 2)

    if average_score >= threshold:
        classification = "ready"
        actions = ["confirm_readiness_evidence", "maintain_current_planning_state"]
        rationale = "The observed average score meets or exceeds the execution threshold."
    elif gap <= 10.0:
        classification = "nearly_ready"
        actions = ["clarify_remaining_success_criteria", "prioritize_smallest_remaining_gaps", "reassess_readiness"]
        rationale = "The observed average score is below the threshold but within a near-readiness band."
    else:
        classification = "not_ready"
        actions = ["clarify_success_criteria", "resolve_highest_impact_candidate_gaps", "reassess_readiness"]
        rationale = "The observed average score is materially below the execution threshold."

    priority = request.get("priority", 0)
    priority = max(0, int(_number(priority, 0)))
    return {
        "capability_id": CAPABILITY_ID,
        "source_capability": SOURCE_CAPABILITY,
        "readiness_assessment": {
            "classification": classification,
            "average_score": round(average_score, 2),
            "execution_threshold": round(threshold, 2),
            "gap_to_threshold": round(gap, 2),
            "score_percent_of_threshold": score_percent,
        },
        "planning_guidance": {
            "priority": priority,
            "rationale": rationale,
            "actions": actions,
            "action_mode": "internal_planning_only",
        },
        "evidence_summary": {
            "affected_candidates": affected,
            "candidate_ids": candidate_ids,
            "unresolved": bool(detail.get("unresolved", False)),
            "reason": detail.get("reason", ""),
        },
        "constraints": {
            "analysis_only": True,
            "execution_performed": False,
            "external_action_performed": False,
            "financial_action_performed": False,
            "approval_or_deployment_state_changed": False,
        },
    }
