"""Pure analytical comparison of explicitly reported capability metrics."""

CAPABILITY_ID='capability_effectiveness_learner'


def capability_manifest():
    return {
        "id": CAPABILITY_ID,
        "title": "Capability Effectiveness Learner",
        "type": "safe_analytical",
        "description": "Compare reported before-and-after metrics without inventing missing evidence.",
        "inputs": ["context with reported metric pairs"],
        "outputs": ["comparisons", "observed_metric_count", "unavailable_metrics"],
        "side_effects": [],
        "safety": {
            "pure_analysis_only": True,
            "does_not_fabricate_evidence": True,
            "no_external_io": True,
            "no_financial_or_approval_actions": True,
        },
    }


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _metric_pairs(context):
    if not isinstance(context, dict):
        return []

    reported = context.get("reported_metrics")
    if isinstance(reported, list):
        pairs = []
        for item in reported:
            if not isinstance(item, dict):
                continue
            name = item.get("name", item.get("metric"))
            before = item.get("baseline", item.get("before"))
            after = item.get("current", item.get("after"))
            if name is not None:
                pairs.append((str(name), before, after))
        return pairs

    if isinstance(reported, dict):
        pairs = []
        for name, values in reported.items():
            if not isinstance(values, dict):
                continue
            before = values.get("baseline", values.get("before"))
            after = values.get("current", values.get("after"))
            pairs.append((str(name), before, after))
        if pairs:
            return pairs

    before_values = None
    after_values = None
    for before_key in ("baseline_metrics", "before_metrics", "baseline", "before"):
        if isinstance(context.get(before_key), dict):
            before_values = context[before_key]
            break
    for after_key in ("current_metrics", "after_metrics", "current", "after"):
        if isinstance(context.get(after_key), dict):
            after_values = context[after_key]
            break
    if isinstance(before_values, dict) and isinstance(after_values, dict):
        return [
            (str(name), before_values.get(name), after_values.get(name))
            for name in before_values.keys()
            if name in after_values
        ]

    metrics = context.get("metrics")
    if isinstance(metrics, list):
        pairs = []
        for item in metrics:
            if not isinstance(item, dict):
                continue
            name = item.get("name", item.get("metric"))
            if name is not None:
                pairs.append((str(name), item.get("before"), item.get("after")))
        return pairs
    return []


def evaluate(context):
    """Return comparisons based only on numeric values explicitly reported in context."""
    comparisons = []
    unavailable = []
    for name, before, after in _metric_pairs(context):
        if not _is_number(before) or not _is_number(after):
            unavailable.append(name)
            continue
        absolute_change = after - before
        if before == 0:
            relative_change = None
            relative_change_status = "undefined_zero_baseline"
        else:
            relative_change = round(absolute_change / abs(before), 10)
            relative_change_status = "reported"
        comparisons.append(
            {
                "metric": name,
                "baseline": before,
                "current": after,
                "absolute_change": absolute_change,
                "relative_change": relative_change,
                "relative_change_status": relative_change_status,
            }
        )
    return {
        "capability_id": CAPABILITY_ID,
        "comparisons": comparisons,
        "observed_metric_count": len(comparisons),
        "unavailable_metrics": unavailable,
        "evidence_status": "reported_only",
    }
