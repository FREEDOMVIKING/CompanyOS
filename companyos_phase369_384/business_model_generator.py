from __future__ import annotations

class BusinessModelGenerator:
    """377: generate plausible monetization models per opportunity."""

    def generate(self, customer, theme):
        models = [
            "monthly SaaS subscription",
            "tiered subscription by usage or seats",
        ]
        if "contractor" in customer or "field-service" in customer:
            models.append("per-job or per-location premium tier")
        if "developer" in customer:
            models.append("API usage pricing")
        return {"primary": models[0], "alternatives": models[1:]}
