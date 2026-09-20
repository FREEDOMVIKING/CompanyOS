CAPABILITY_ID='app_mvp_scope_optimizer'


def capability_manifest():
    return {
        "id": CAPABILITY_ID,
        "title": "App Mvp Scope Optimizer",
        "version": "1.0.0",
        "kind": "safe_analytical",
        "description": "Ranks supplied app concepts by evidence quality and recommends the smallest measurable paid-validation scope.",
        "purity": "deterministic_context_only",
        "side_effects": [],
        "required_inputs": ["context"],
        "outputs": [
            "candidate_assessments",
            "recommended_scope",
            "validation_plan",
            "evidence_gaps",
            "decision"
        ]
    }


def _text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _items(value):
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _candidate_records(context):
    direct = context.get("candidates") if isinstance(context, dict) else None
    if isinstance(direct, list):
        return direct
    profit = context.get("profit", {}) if isinstance(context, dict) else {}
    nested = profit.get("candidates") if isinstance(profit, dict) else None
    return nested if isinstance(nested, list) else []


def _has_any(record, keys):
    for key in keys:
        value = record.get(key)
        if value not in (None, "", [], {}, False):
            return True
    return False


def _assessment(record, position):
    if not isinstance(record, dict):
        record = {"name": _text(record)}
    name = _text(record.get("name") or record.get("title") or record.get("id") or "Unnamed candidate")
    dimensions = {
        "problem_specificity": _has_any(record, ("problem", "pain", "job_to_be_done", "problem_statement")),
        "reachable_buyer": _has_any(record, ("buyer", "customer", "audience", "target_customer", "market")),
        "value_signal": _has_any(record, ("value", "benefit", "outcome", "roi", "value_proposition")),
        "behavior_evidence": _has_any(record, ("evidence", "validation", "interviews", "usage", "demand_signal")),
        "paid_signal": _has_any(record, ("price", "pricing", "paid_pilot", "purchase_intent", "revenue_signal")),
        "delivery_feasibility": _has_any(record, ("workflow", "prototype", "integration", "delivery", "implementation"))
    }
    score = sum(1 for present in dimensions.values() if present)
    gaps = [key for key, present in dimensions.items() if not present]
    return {
        "position": position,
        "id": _text(record.get("id")),
        "name": name,
        "evidence_score": score,
        "evidence_max": len(dimensions),
        "dimensions": dimensions,
        "evidence_gaps": gaps,
        "source": _text(record.get("source")),
        "supplied_score": record.get("score") if isinstance(record.get("score"), (int, float)) else None
    }


def _scope_for(best):
    if best is None:
        audience = "one explicitly named buyer segment"
        job = "one painful, observable workflow"
    else:
        audience = "the buyer segment supported by the supplied evidence"
        job = "the single workflow represented by the strongest evidence"
    return {
        "audience": audience,
        "job_to_be_done": job,
        "included": [
            "one core workflow",
            "one narrow user role",
            "one observable outcome",
            "manual or low-code fulfillment where acceptable",
            "a price or purchase-intent test"
        ],
        "excluded": [
            "secondary personas",
            "unvalidated integrations",
            "broad automation",
            "multi-sided marketplace behavior",
            "custom administration and edge-case features"
        ],
        "success_condition": "A defined buyer completes the chosen validation action and provides a measurable paid signal without unsupported assumptions."
    }


def evaluate(context):
    if not isinstance(context, dict):
        context = {}
    records = _candidate_records(context)
    assessments = [_assessment(record, index + 1) for index, record in enumerate(records)]
    ranked = sorted(assessments, key=lambda item: (-item["evidence_score"], item["position"]))
    best = ranked[0] if ranked else None
    profit = context.get("profit", {})
    if not isinstance(profit, dict):
        profit = {}
    candidate_count = profit.get("candidate_count")
    if not isinstance(candidate_count, int):
        candidate_count = len(records)
    global_gaps = []
    if not records:
        global_gaps.extend(["candidate_records", "problem_specificity", "reachable_buyer", "paid_signal"])
    else:
        for assessment in assessments:
            for gap in assessment["evidence_gaps"]:
                if gap not in global_gaps:
                    global_gaps.append(gap)
    decision = "scope_candidate" if best and best["evidence_score"] >= 4 else "research_more"
    if best is None:
        decision_reason = "No candidate records were supplied; do not select or fabricate a winner."
    elif decision == "research_more":
        decision_reason = "The strongest supplied candidate lacks enough evidence for a focused paid-validation scope."
    else:
        decision_reason = "The strongest supplied candidate has enough stated evidence to define a narrow test, but this is not proof of demand."
    return {
        "capability_id": CAPABILITY_ID,
        "status": "ok",
        "decision": decision,
        "decision_reason": decision_reason,
        "candidate_count": candidate_count,
        "assessed_count": len(assessments),
        "candidate_assessments": ranked,
        "selected_candidate": best,
        "recommended_scope": _scope_for(best),
        "validation_plan": [
            {"step": 1, "measure": "qualified problem conversations", "target": "at least 5 defined buyers", "evidence_required": "recorded problem and current workaround"},
            {"step": 2, "measure": "workflow commitment", "target": "at least 3 buyers complete the proposed workflow", "evidence_required": "observable completion, not stated interest"},
            {"step": 3, "measure": "paid signal", "target": "at least 1 buyer accepts the stated offer or paid pilot", "evidence_required": "buyer-confirmed commitment; no inferred revenue"},
            {"step": 4, "measure": "delivery burden", "target": "manual effort and blockers documented", "evidence_required": "actual test log"}
        ],
        "evidence_gaps": global_gaps,
        "guardrails": [
            "Use only evidence present in context.",
            "Do not treat a supplied score as proof of demand or probability.",
            "Do not claim a winner when evidence is insufficient.",
            "Keep payment collection, approvals, credentials, and deployment outside this analytical capability."
        ]
    }
