from __future__ import annotations

class MarketThesisBuilder:
    """381: build a concise market thesis from enriched evidence."""

    def build(self, item):
        return {
            "name": item["name"],
            "customer": item["customer"],
            "core_problem": item["problem"],
            "why_now": "Repeated public pain signals indicate an active unresolved workflow problem.",
            "evidence_strength": item["agreement"],
            "pain_severity": item["pain_severity"],
            "problem_frequency": item["problem_frequency"],
            "willingness_to_pay": item["willingness_to_pay"],
            "business_model": item["business_model"],
            "startup_estimate": item["startup_estimate"],
            "time_to_revenue": item["time_to_revenue"],
            "replacement_analysis": item["replacement_analysis"],
            "evidence_links": item["evidence_links"][:10],
        }
