"""Transparent, pure analysis for comparing venture opportunities."""
import math
from typing import Any

CAPABILITY_ID='risk_adjusted_venture_evaluator'


def capability_manifest() -> dict:
    return {
        "id": CAPABILITY_ID,
        "name": "Risk-adjusted venture evaluator",
        "version": "1.0",
        "description": "Evaluates explicit evidence and assumptions using confidence-weighted scenario ranges.",
        "pure_analysis": True,
    }


def _number(value: Any):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value), 1.0, "unspecified"
    if isinstance(value, dict):
        raw = value.get("value", value.get("amount", value.get("estimate")))
        parsed = _number(raw)
        if parsed is None:
            return None
        confidence = value.get("confidence", value.get("certainty", 1.0))
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 1.0
        if confidence > 1:
            confidence /= 100.0
        confidence = max(0.0, min(1.0, confidence))
        source = "sourced" if value.get("source") or value.get("evidence") else "assumption"
        return parsed[0], confidence, source
    return None


def _find(context: dict, names):
    for name in names:
        if name in context:
            parsed = _number(context[name])
            if parsed is not None:
                return parsed
    for section_name in ("market_evidence", "operating_assumptions", "pricing", "costs", "validation_results", "delivery_constraints", "evidence", "assumptions"):
        section = context.get(section_name)
        if isinstance(section, dict):
            for name in names:
                if name in section:
                    parsed = _number(section[name])
                    if parsed is not None:
                        return parsed
    return None


def _probability(context: dict):
    item = _find(context, ("probability_of_success", "success_probability", "probability", "conversion_probability"))
    if item is None:
        return None
    value, confidence, source = item
    if value > 1:
        value /= 100.0
    return max(0.0, min(1.0, value)), confidence, source


def _fit(context: dict):
    item = _find(context, ("business_model_fit", "model_fit", "fit_score", "product_market_fit"))
    if item is None:
        return None
    value, confidence, source = item
    if value > 1:
        value /= 100.0
    return max(0.0, min(1.0, value)), confidence, source


def _money(context: dict):
    price = _find(context, ("price", "unit_price", "average_price", "selling_price"))
    units = _find(context, ("units", "customers", "orders", "sales", "expected_units", "volume"))
    variable = _find(context, ("variable_cost", "unit_cost", "cost_per_unit", "delivery_cost_per_unit"))
    fixed = _find(context, ("fixed_cost", "operating_cost", "setup_cost", "monthly_fixed_cost"))
    if price is None or units is None:
        return None
    revenue = price[0] * units[0]
    costs = (variable[0] * units[0] if variable else 0.0) + (fixed[0] if fixed else 0.0)
    confidence_parts = [price[1], units[1]] + ([variable[1]] if variable else []) + ([fixed[1]] if fixed else [])
    confidence = sum(confidence_parts) / len(confidence_parts)
    sources = [x[2] for x in (price, units, variable, fixed) if x is not None]
    return revenue - costs, confidence, sources, {"revenue": revenue, "costs": costs}


def _scenario(name, profit_data, probability, fit, unknowns):
    reasons = list(unknowns)
    profit = None
    confidence = 0.0
    if profit_data is not None:
        profit = profit_data[0] * (probability[0] if probability is not None else 1.0)
        confidence = profit_data[1] * (probability[1] if probability is not None else 1.0)
    return {
        "name": name,
        "profit": profit,
        "realized_profit": profit,
        "probability_of_success": probability[0] if probability else None,
        "business_model_fit": fit[0] if fit else None,
        "confidence": round(confidence, 6),
        "reasons": reasons,
        "unknowns": list(reasons),
    }


def evaluate(context: dict) -> dict:
    if not isinstance(context, dict):
        context = {}
    money = _money(context)
    probability = _probability(context)
    fit = _fit(context)
    unknowns = []
    if money is None:
        unknowns.append("inputs_unknown")
    if fit is None:
        unknowns.append("fit_unestimated")
    base = _scenario("known", money, probability, fit, unknowns)
    scenarios = {"known": base, "conservative": dict(base), "optimistic": dict(base)}
    for key in ("conservative", "optimistic"):
        scenarios[key]["name"] = key
    if money is not None:
        scenarios["conservative"]["profit"] = money[0] * (probability[0] if probability else 1.0)
        scenarios["optimistic"]["profit"] = scenarios["conservative"]["profit"]
        scenarios["conservative"]["realized_profit"] = scenarios["conservative"]["profit"]
        scenarios["optimistic"]["realized_profit"] = scenarios["optimistic"]["profit"]
    evidence = []
    assumptions = []
    for section in ("market_evidence", "validation_results", "evidence"):
        if section in context:
            evidence.append(section)
    for section in ("operating_assumptions", "pricing", "costs", "assumptions"):
        if section in context:
            assumptions.append(section)
    return {
        "capability_id": CAPABILITY_ID,
        "scenarios": scenarios,
        "profit_range": [base["profit"], base["profit"]] if base["profit"] is not None else [None, None],
        "evidence_sections": evidence,
        "assumption_sections": assumptions,
        "unknowns": unknowns,
        "ranking_score": base["profit"],
    }
