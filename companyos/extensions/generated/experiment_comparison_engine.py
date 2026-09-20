import math

CAPABILITY_ID='experiment_comparison_engine'


def capability_manifest():
    return {
        "id": CAPABILITY_ID,
        "title": "Experiment Comparison Engine",
        "version": "1.0.0",
        "kind": "safe_analytical",
        "pure": True,
        "side_effects": [],
        "required_inputs": ["experiments"],
        "outputs": ["comparisons", "ranking", "evidence_summary"],
    }


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def _metric_records(experiment):
    records = []
    observations = experiment.get("observations", [])
    if isinstance(observations, dict):
        observations = [observations]
    if isinstance(observations, list):
        for observation in observations:
            if not isinstance(observation, dict):
                continue
            metric = observation.get("metric") or observation.get("name")
            value = observation.get("value")
            if isinstance(value, list):
                for item in value:
                    number = _number(item)
                    if metric and number is not None:
                        records.append((str(metric), number, observation.get("sample_size")))
            else:
                number = _number(value)
                if metric and number is not None:
                    records.append((str(metric), number, observation.get("sample_size")))
    metrics = experiment.get("metrics", {})
    if isinstance(metrics, dict):
        for metric, raw in metrics.items():
            direction = None
            sample_size = None
            values = raw
            if isinstance(raw, dict):
                values = raw.get("value", raw.get("values"))
                direction = raw.get("direction")
                sample_size = raw.get("sample_size")
            if not isinstance(values, list):
                values = [values]
            for value in values:
                number = _number(value)
                if number is not None:
                    records.append((str(metric), number, sample_size, direction))
    normalized = []
    for record in records:
        if len(record) == 3:
            normalized.append((record[0], record[1], record[2], None))
        else:
            normalized.append(record)
    return normalized


def _directions(context):
    configured = context.get("metric_directions", {})
    return configured if isinstance(configured, dict) else {}


def _summarize(experiment, context):
    grouped = {}
    for metric, value, sample_size, local_direction in _metric_records(experiment):
        entry = grouped.setdefault(metric, {"values": [], "sample_sizes": [], "direction": None})
        entry["values"].append(value)
        if _number(sample_size) is not None:
            entry["sample_sizes"].append(_number(sample_size))
        if local_direction in ("higher", "lower"):
            entry["direction"] = local_direction
    directions = _directions(context)
    result = {}
    for metric, entry in grouped.items():
        values = entry["values"]
        direction = entry["direction"] or directions.get(metric, "higher")
        if direction not in ("higher", "lower"):
            direction = "higher"
        result[metric] = {
            "value": sum(values) / len(values),
            "observation_count": len(values),
            "sample_size_total": sum(entry["sample_sizes"]) if entry["sample_sizes"] else None,
            "direction": direction,
            "min": min(values),
            "max": max(values),
        }
    return result


def evaluate(context):
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    experiments = context.get("experiments", context.get("bets", []))
    if not isinstance(experiments, list):
        raise ValueError("experiments must be a list")
    summaries = []
    for index, experiment in enumerate(experiments):
        if not isinstance(experiment, dict):
            continue
        experiment_id = experiment.get("id", "experiment-{}".format(index + 1))
        summaries.append({
            "id": str(experiment_id),
            "name": experiment.get("name", str(experiment_id)),
            "metrics": _summarize(experiment, context),
            "evidence_records": len(_metric_records(experiment)),
        })

    metric_sets = [set(item["metrics"]) for item in summaries if item["metrics"]]
    shared_metrics = sorted(set.intersection(*metric_sets)) if metric_sets else []
    ranges = {}
    for metric in shared_metrics:
        values = [item["metrics"][metric]["value"] for item in summaries]
        ranges[metric] = (min(values), max(values))

    comparisons = []
    for item in summaries:
        normalized_values = []
        for metric in shared_metrics:
            metric_data = item["metrics"][metric]
            low, high = ranges[metric]
            if high == low:
                normalized = 1.0
            else:
                normalized = (metric_data["value"] - low) / (high - low)
                if metric_data["direction"] == "lower":
                    normalized = 1.0 - normalized
            normalized_values.append(normalized)
        comparability = (len(shared_metrics) / len(set().union(*(set(x["metrics"]) for x in summaries)))) if summaries and set().union(*(set(x["metrics"]) for x in summaries)) else 0.0
        derived_score = sum(normalized_values) / len(normalized_values) if normalized_values else None
        comparisons.append({
            "id": item["id"],
            "name": item["name"],
            "shared_metric_count": len(shared_metrics),
            "evidence_records": item["evidence_records"],
            "comparability_index": round(comparability, 6),
            "observed_metric_index": round(derived_score, 6) if derived_score is not None else None,
            "metrics": item["metrics"],
        })

    ranked = sorted(
        [item for item in comparisons if item["observed_metric_index"] is not None],
        key=lambda item: (-item["observed_metric_index"], -item["evidence_records"], item["id"]),
    )
    ranking = [item["id"] for item in ranked]
    decision = "ranked_on_observed_metrics" if ranking and shared_metrics else "insufficient_comparable_evidence"
    return {
        "capability_id": CAPABILITY_ID,
        "decision": decision,
        "shared_metrics": shared_metrics,
        "comparisons": comparisons,
        "ranking": ranking,
        "evidence_summary": {
            "experiment_count": len(summaries),
            "experiments_with_observations": sum(1 for item in summaries if item["evidence_records"] > 0),
            "shared_metric_count": len(shared_metrics),
            "fabricated_values": False,
            "probabilities_estimated": False,
        },
    }
