from __future__ import annotations
from typing import Any, Dict, List

class RevenueOperator:
    """142: optimize pricing/offer scenarios and revenue plans without moving funds."""

    def evaluate(self, offers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for offer in offers:
            price = max(0.0, float(offer.get("price", 0)))
            expected_customers = max(0.0, float(offer.get("expected_customers", 0)))
            variable_cost = max(0.0, float(offer.get("variable_cost", 0)))
            conversion = max(0.0, min(1.0, float(offer.get("conversion", 0))))
            revenue = price * expected_customers * conversion
            contribution = max(0.0, price - variable_cost) * expected_customers * conversion
            out.append({
                **offer,
                "expected_revenue": round(revenue, 2),
                "expected_contribution": round(contribution, 2),
                "funds_moved": False,
            })
        return sorted(out, key=lambda x: x["expected_contribution"], reverse=True)
