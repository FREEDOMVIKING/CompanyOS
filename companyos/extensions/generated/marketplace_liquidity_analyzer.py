"""Pure analysis for marketplace supply-demand liquidity."""

import math


CAPABILITY_ID='marketplace_liquidity_analyzer'


def capability_manifest():
    return {
        "id": CAPABILITY_ID,
        "title": "Marketplace Liquidity Analyzer",
        "version": "1.0.0",
        "kind": "analytical",
        "pure": True,
        "inputs": ["observations"],
        "outputs": ["summary", "segments", "evidence_quality", "limitations"],
    }


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    if not math.isfinite(value) or value < 0:
        return None
    return value


def _text(value):
    if isinstance(value, str):
        value = value.strip()
        if value:
            return value[:120]
    return "all"


def _rows(context):
    if not isinstance(context, dict):
        return []
    source = context.get("observations")
    if source is None:
        source = context.get("records")
    if source is None:
        source = context.get("data")
    if isinstance(source, dict):
        source = [source]
    if not isinstance(source, list):
        source = []
    rows = []
    for item in source:
        if isinstance(item, dict):
            rows.append(item)
    if not rows:
        direct_supply = _number(context.get("supply"))
        direct_demand = _number(context.get("demand"))
        if direct_supply is not None or direct_demand is not None:
            rows.append({"supply": direct_supply, "demand": direct_demand})
    return rows


def _value(item, names):
    for name in names:
        value = _number(item.get(name))
        if value is not None:
            return value
    return None


def _segment_stats(rows):
    groups = {}
    for item in rows:
        supply = _value(item, ("supply", "sellers", "available_supply", "listing_count"))
        demand = _value(item, ("demand", "buyers", "buyer_interest", "searches"))
        if supply is None or demand is None:
            continue
        segment = _text(item.get("segment", item.get("category", item.get("market"))))
        group = groups.setdefault(segment, {"supply": 0.0, "demand": 0.0, "transactions": 0.0, "transaction_rows": 0, "rows": 0, "sources": 0})
        group["supply"] += supply
        group["demand"] += demand
        group["rows"] += 1
        transactions = _value(item, ("transactions", "completed_transactions", "matches"))
        if transactions is not None:
            group["transactions"] += transactions
            group["transaction_rows"] += 1
        source = item.get("source")
        if isinstance(source, str) and source.strip():
            group["sources"] += 1
    return groups


def _result_for(name, group):
    supply = group["supply"]
    demand = group["demand"]
    unmet = max(demand - supply, 0.0)
    ratio = demand / supply if supply > 0 else (float("inf") if demand > 0 else 1.0)
    if demand == 0 and supply > 0:
        balance = "oversupplied"
    elif supply == 0 and demand > 0:
        balance = "unserved_demand"
    elif demand > supply:
        balance = "demand_heavy"
    elif supply > demand:
        balance = "supply_heavy"
    else:
        balance = "balanced"
    observed_transactions = group["transaction_rows"] > 0
    opportunity = min(100.0, (unmet / max(demand, 1.0)) * 70.0 + min(group["transactions"], demand) / max(demand, 1.0) * 30.0) if demand > 0 else 0.0
    confidence = min(1.0, group["rows"] / 5.0)
    if observed_transactions:
        confidence = min(1.0, confidence + 0.2)
    return {
        "segment": name,
        "supply": supply,
        "demand": demand,
        "unmet_demand": unmet,
        "demand_supply_ratio": None if math.isinf(ratio) else round(ratio, 4),
        "balance": balance,
        "observed_transactions": group["transactions"] if observed_transactions else None,
        "opportunity_score": round(opportunity, 2),
        "confidence": round(confidence, 2),
        "evidence": {
            "observation_count": group["rows"],
            "transaction_observation_count": group["transaction_rows"],
            "source_count": group["sources"],
        },
    }


def evaluate(context):
    """Return a deterministic liquidity assessment without side effects."""
    rows = _rows(context)
    groups = _segment_stats(rows)
    if not groups:
        return {
            "capability_id": CAPABILITY_ID,
            "status": "insufficient_evidence",
            "summary": {"supply": 0.0, "demand": 0.0, "unmet_demand": 0.0, "opportunity_score": None, "confidence": 0.0},
            "segments": [],
            "evidence_quality": {"valid_observation_count": 0, "source_count": 0, "transaction_coverage": 0.0},
            "limitations": ["At least one observation with nonnegative supply and demand is required."],
        }
    segments = [_result_for(name, groups[name]) for name in sorted(groups)]
    supply = sum(item["supply"] for item in segments)
    demand = sum(item["demand"] for item in segments)
    unmet = sum(item["unmet_demand"] for item in segments)
    transaction_values = [item["observed_transactions"] for item in segments if item["observed_transactions"] is not None]
    score = sum(item["opportunity_score"] * item["demand"] for item in segments) / demand if demand else 0.0
    confidence = sum(item["confidence"] * item["demand"] for item in segments) / demand if demand else 0.0
    source_count = sum(item["evidence"]["source_count"] for item in segments)
    coverage = len(transaction_values) / len(segments)
    return {
        "capability_id": CAPABILITY_ID,
        "status": "analysed",
        "summary": {"supply": supply, "demand": demand, "unmet_demand": unmet, "opportunity_score": round(score, 2), "confidence": round(confidence, 2)},
        "segments": segments,
        "evidence_quality": {"valid_observation_count": sum(item["evidence"]["observation_count"] for item in segments), "source_count": source_count, "transaction_coverage": round(coverage, 2)},
        "limitations": ["Opportunity score indicates observed imbalance, not guaranteed conversion or profit.", "Missing or invalid fields are excluded rather than inferred."],
    }
