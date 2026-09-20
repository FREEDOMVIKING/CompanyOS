CAPABILITY_ID='app_problem_ranker'


def capability_manifest():
    return {
        "id": CAPABILITY_ID,
        "title": "App Problem Ranker",
        "version": "1.0.0",
        "type": "safe_analytical",
        "pure": True,
        "inputs": {"context": "mapping containing problems or candidates"},
        "outputs": {"ranked_problems": "evidence-based ordered problem records"},
        "dimensions": ["pain", "frequency", "price", "competition"],
        "safety": {
            "network": False,
            "shell": False,
            "file_writes": False,
            "external_sends": False,
            "financial_actions": False,
            "approval_actions": False,
            "deployment_actions": False,
        },
    }


_WEIGHTS = {
    "pain": 0.30,
    "frequency": 0.25,
    "price": 0.25,
    "competition": 0.20,
}

_ALIASES = {
    "pain": ("pain_score", "pain", "pain_intensity"),
    "frequency": ("frequency_score", "frequency", "occurrence_score"),
    "price": ("price_score", "willingness_to_pay_score", "price"),
    "competition": ("competition_score", "competition", "competitive_intensity"),
}


def _number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if value != value:
            return None
        return float(value)
    if isinstance(value, dict):
        for key in ("score", "value"):
            if key in value:
                return _number(value[key])
    return None


def _score(value):
    number = _number(value)
    if number is None:
        return None
    if 0.0 <= number <= 10.0:
        number *= 10.0
    if number < 0.0 or number > 100.0:
        return None
    return round(number, 4)


def _items(context):
    if not isinstance(context, dict):
        return []
    for key in ("problems", "candidates", "opportunities"):
        value = context.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _identity(item):
    for key in ("id", "problem_id", "candidate_id"):
        if item.get(key) is not None:
            return item[key]
    return None


def _name(item):
    for key in ("name", "title", "problem", "label"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _dimension_scores(item):
    scores = {}
    source_keys = {}
    nested = item.get("scores")
    if not isinstance(nested, dict):
        nested = {}
    for dimension, aliases in _ALIASES.items():
        found = None
        found_key = None
        for key in aliases:
            if key in item:
                found = item[key]
                found_key = key
                break
            if key in nested:
                found = nested[key]
                found_key = "scores." + key
                break
        scores[dimension] = _score(found)
        source_keys[dimension] = found_key
    return scores, source_keys


def _rank_record(item, position):
    scores, source_keys = _dimension_scores(item)
    available = [key for key, value in scores.items() if value is not None]
    contributions = {}
    weighted_total = 0.0
    weight_total = 0.0
    for dimension, weight in _WEIGHTS.items():
        value = scores[dimension]
        if value is None:
            continue
        adjusted = 100.0 - value if dimension == "competition" else value
        contributions[dimension] = round(adjusted * weight, 4)
        weighted_total += adjusted * weight
        weight_total += weight
    rank_score = round(weighted_total / weight_total, 4) if weight_total else None
    return {
        "problem_id": _identity(item),
        "name": _name(item),
        "rank_score": rank_score,
        "rankable": rank_score is not None,
        "evidence_status": "partial" if 0 < len(available) < 4 else ("complete" if len(available) == 4 else "insufficient"),
        "dimensions": scores,
        "competition_interpretation": "higher supplied competition lowers opportunity score",
        "contributions": contributions,
        "evidence_keys": source_keys,
        "source": item.get("source") if isinstance(item.get("source"), str) else None,
        "input_position": position,
    }


def evaluate(context):
    if not isinstance(context, dict):
        return {
            "capability_id": CAPABILITY_ID,
            "ranked_problems": [],
            "unscored_problems": [],
            "errors": ["context must be a mapping"],
        }
    records = [_rank_record(item, index) for index, item in enumerate(_items(context))]
    ranked = [record for record in records if record["rankable"]]
    unscored = [record for record in records if not record["rankable"]]
    ranked.sort(key=lambda record: (-record["rank_score"], record["input_position"]))
    return {
        "capability_id": CAPABILITY_ID,
        "method": {
            "weights": dict(_WEIGHTS),
            "scale": "0-100; supplied 0-10 values are expanded to 0-100",
            "missing_data": "excluded from the weighted denominator and never fabricated",
            "competition": "treated as competitive intensity and inverted",
        },
        "ranked_problems": ranked,
        "unscored_problems": unscored,
        "counts": {"input": len(records), "ranked": len(ranked), "unscored": len(unscored)},
        "errors": [],
    }
