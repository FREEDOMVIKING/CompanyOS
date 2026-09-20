CAPABILITY_ID='service_offer_ranker'


_DIMENSIONS = ("urgency", "price", "labor_intensity", "sales_friction")
_ALIASES = {
    "urgency": ("urgency", "urgency_score", "priority", "priority_score"),
    "price": ("price", "price_usd", "price_cents", "unit_price", "offer_price", "estimated_price"),
    "labor_intensity": ("labor_intensity", "labor", "labor_score", "delivery_labor", "labor_intensity_score"),
    "sales_friction": ("sales_friction", "sales", "sales_score", "sales_effort", "sales_friction_score"),
}


def capability_manifest():
    return {
        "id": CAPABILITY_ID,
        "title": "Service Offer Ranker",
        "version": "1.0.0",
        "mode": "pure_analysis",
        "description": "Ranks service offers using supplied urgency, price, labor intensity, and sales friction evidence.",
        "dimensions": list(_DIMENSIONS),
        "does_not_fabricate_missing_dimensions": True,
    }


def _offers_from_context(context):
    if isinstance(context, list):
        return context
    if not isinstance(context, dict):
        return []
    for key in ("services", "offers", "service_offers", "items", "candidates"):
        value = context.get(key)
        if isinstance(value, list):
            return value
    return []


def _value_for(item, dimension):
    if not isinstance(item, dict):
        return None, False
    lowered = {str(key).lower(): value for key, value in item.items()}
    for alias in _ALIASES[dimension]:
        if alias in lowered and lowered[alias] is not None:
            return lowered[alias], True
    return None, False


def _number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().replace(",", "")
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None
    return None


def _bounded_scale(value, dimension):
    if dimension == "price":
        return value
    if 0.0 <= value <= 1.0:
        return value * 100.0
    if 1.0 < value <= 5.0:
        return value * 20.0
    if 5.0 < value <= 10.0:
        return value * 10.0
    return value


def _label(item, index):
    if isinstance(item, dict):
        for key in ("name", "title", "service", "id"):
            value = item.get(key)
            if value is not None and str(value).strip():
                return value
    return "service_%d" % (index + 1)


def evaluate(context):
    offers = _offers_from_context(context)
    ranked = []
    unranked = []
    prepared = []

    for index, original in enumerate(offers):
        item = original if isinstance(original, dict) else {"value": original}
        values = {}
        missing = []
        invalid = []
        for dimension in _DIMENSIONS:
            raw, present = _value_for(item, dimension)
            if not present:
                missing.append(dimension)
                continue
            numeric = _number(raw)
            if numeric is None:
                invalid.append(dimension)
            else:
                values[dimension] = _bounded_scale(numeric, dimension)

        entry = dict(item)
        entry.setdefault("name", _label(item, index))
        if missing or invalid:
            entry["missing_dimensions"] = missing
            if invalid:
                entry["invalid_dimensions"] = invalid
            unranked.append(entry)
            continue
        prepared.append((entry, values, index))

    prices = [values["price"] for _, values, _ in prepared]
    maximum_price = max(prices) if prices else 0.0
    for entry, values, index in prepared:
        price_score = 0.0 if maximum_price <= 0.0 else (values["price"] / maximum_price) * 100.0
        urgency_score = max(0.0, min(100.0, values["urgency"]))
        labor_score = max(0.0, min(100.0, values["labor_intensity"]))
        friction_score = max(0.0, min(100.0, values["sales_friction"]))
        score = (
            urgency_score * 0.30
            + price_score * 0.30
            + (100.0 - labor_score) * 0.20
            + (100.0 - friction_score) * 0.20
        )
        ranked_entry = dict(entry)
        ranked_entry["score"] = round(score, 4)
        ranked_entry["score_components"] = {
            "urgency": round(urgency_score, 4),
            "price": round(price_score, 4),
            "labor_intensity": round(100.0 - labor_score, 4),
            "sales_friction": round(100.0 - friction_score, 4),
        }
        ranked_entry["rank"] = 0
        ranked.append((ranked_entry, index))

    ranked.sort(key=lambda pair: (-pair[0]["score"], str(pair[0].get("name", "")), pair[1]))
    final_ranked = []
    for rank, (entry, _) in enumerate(ranked, 1):
        entry["rank"] = rank
        final_ranked.append(entry)

    return {
        "capability_id": CAPABILITY_ID,
        "ranked": final_ranked,
        "unranked": unranked,
        "dimension_order": list(_DIMENSIONS),
        "ranking_method": "urgency_and_relative_price_positive; labor_and_sales_friction_inverse",
    }
