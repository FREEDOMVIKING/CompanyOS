"""Pure, evidence-bounded buyer-seller matching analysis."""

from math import isfinite
from typing import Any, Dict, Iterable, List, Mapping, Sequence

CAPABILITY_ID='marketplace_matching_engine'


def capability_manifest() -> Dict[str, Any]:
    return {
        "id": CAPABILITY_ID,
        "title": "Marketplace Matching Engine",
        "version": "1.0.0",
        "mode": "pure_analysis",
        "inputs": ["buyers", "sellers"],
        "outputs": ["ranked_matches", "evidence", "limitations"],
        "side_effects": [],
        "evidence_policy": "Use only explicitly supplied fields; missing evidence lowers confidence and is reported.",
    }


def _as_records(value: Any) -> List[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _text(value: Any) -> str:
    return value.strip().casefold() if isinstance(value, str) else ""


def _values(record: Mapping[str, Any], keys: Iterable[str]) -> set[str]:
    result: set[str] = set()
    for key in keys:
        value = record.get(key)
        items = value if isinstance(value, (list, tuple, set)) else [value]
        for item in items:
            if isinstance(item, str) and item.strip():
                result.add(item.strip().casefold())
    return result


def _number(record: Mapping[str, Any], keys: Iterable[str]) -> float | None:
    for key in keys:
        value = record.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)) and isfinite(float(value)):
            return float(value)
    return None


def _identifier(record: Mapping[str, Any], prefix: str, index: int) -> str:
    value = record.get("id", record.get("key"))
    if isinstance(value, (str, int, float)) and not isinstance(value, bool):
        text = str(value).strip()
        if text:
            return text
    return f"{prefix}:{index}"


def _label(record: Mapping[str, Any], identifier: str) -> str:
    for key in ("name", "title", "label"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return identifier


def _pair(buyer: Mapping[str, Any], seller: Mapping[str, Any], buyer_id: str, seller_id: str) -> Dict[str, Any]:
    score = 0.0
    evidence: List[Dict[str, Any]] = []
    missing: List[str] = []

    buyer_categories = _values(buyer, ("category", "categories", "industry", "industries", "needs"))
    seller_categories = _values(seller, ("category", "categories", "industry", "industries", "services"))
    if buyer_categories and seller_categories:
        overlap = sorted(buyer_categories & seller_categories)
        if overlap:
            score += 25.0
            evidence.append({"dimension": "category", "value": overlap, "points": 25.0})
        else:
            evidence.append({"dimension": "category", "value": [], "points": 0.0})
    else:
        missing.append("category")

    buyer_geo = _values(buyer, ("geography", "location", "region", "regions", "market"))
    seller_geo = _values(seller, ("geography", "location", "region", "regions", "market"))
    if buyer_geo and seller_geo:
        overlap = sorted(buyer_geo & seller_geo)
        if overlap:
            score += 15.0
            evidence.append({"dimension": "geography", "value": overlap, "points": 15.0})
        else:
            evidence.append({"dimension": "geography", "value": [], "points": 0.0})
    else:
        missing.append("geography")

    requirements = _values(buyer, ("requirements", "required_capabilities", "capabilities", "skills"))
    capabilities = _values(seller, ("capabilities", "skills", "services", "offerings"))
    if requirements and capabilities:
        overlap = sorted(requirements & capabilities)
        ratio = len(overlap) / len(requirements)
        points = round(20.0 * ratio, 2)
        score += points
        evidence.append({"dimension": "capability", "value": overlap, "required_count": len(requirements), "points": points})
    else:
        missing.append("capability")

    buyer_tags = _values(buyer, ("tags", "preferences"))
    seller_tags = _values(seller, ("tags", "specialties"))
    if buyer_tags and seller_tags:
        overlap = sorted(buyer_tags & seller_tags)
        points = 10.0 if overlap else 0.0
        score += points
        evidence.append({"dimension": "tags", "value": overlap, "points": points})
    else:
        missing.append("tags")

    budget = _number(buyer, ("budget_max", "max_budget", "budget"))
    price = _number(seller, ("price", "asking_price", "seller_price"))
    if budget is not None and price is not None and budget >= 0 and price >= 0:
        if price <= budget:
            points = 30.0 if budget == 0 and price == 0 else round(30.0 * (1.0 - price / budget), 2) if budget else 0.0
            points = max(0.0, min(30.0, points))
            score += points
        else:
            points = 0.0
        evidence.append({"dimension": "economic_fit", "buyer_budget_max": budget, "seller_price": price, "points": points})
    else:
        missing.append("economic_fit")

    observed = len(evidence)
    confidence = round(observed / 5.0, 2)
    status = "rankable" if observed else "insufficient_evidence"
    return {
        "buyer_id": buyer_id,
        "buyer_name": _label(buyer, buyer_id),
        "seller_id": seller_id,
        "seller_name": _label(seller, seller_id),
        "score": round(score, 2),
        "confidence": confidence,
        "status": status,
        "evidence": evidence,
        "missing_evidence": sorted(set(missing)),
    }


def evaluate(context: Mapping[str, Any]) -> Dict[str, Any]:
    """Return deterministic rankings from explicit buyer and seller records."""
    if not isinstance(context, Mapping):
        raise TypeError("context must be a mapping")
    source = context.get("marketplace", context)
    if not isinstance(source, Mapping):
        source = {}
    buyers = _as_records(source.get("buyers", []))
    sellers = _as_records(source.get("sellers", []))
    matches: List[Dict[str, Any]] = []
    for buyer_index, buyer in enumerate(buyers):
        buyer_id = _identifier(buyer, "buyer", buyer_index)
        for seller_index, seller in enumerate(sellers):
            seller_id = _identifier(seller, "seller", seller_index)
            matches.append(_pair(buyer, seller, buyer_id, seller_id))
    matches.sort(key=lambda item: (-item["score"], -item["confidence"], item["buyer_id"], item["seller_id"]))
    top_k = source.get("top_k")
    if isinstance(top_k, int) and not isinstance(top_k, bool) and top_k >= 0:
        matches = matches[:top_k]
    return {
        "capability_id": CAPABILITY_ID,
        "buyer_count": len(buyers),
        "seller_count": len(sellers),
        "match_count": len(matches),
        "ranked_matches": matches,
        "limitations": [
            "Scores reflect only explicitly supplied fit and price evidence.",
            "Missing fields are not inferred and reduce confidence.",
            "This result is analytical only; it does not contact parties, transact, approve, or execute changes.",
        ],
    }
