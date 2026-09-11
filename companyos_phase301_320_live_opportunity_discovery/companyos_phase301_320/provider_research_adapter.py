from __future__ import annotations
import json
from companyos_phase269_276 import ResilientOpenRouterAdapter

class ProviderResearchAdapter:
    """317: optional model-assisted opportunity synthesis using existing OpenRouter.

    This adapter reasons over evidence supplied to it. It does not claim to browse
    the public internet by itself; live source collection remains pluggable.
    """

    def __init__(self, adapter=None):
        self.adapter = adapter or ResilientOpenRouterAdapter()

    @property
    def configured(self):
        return self.adapter.configured

    def synthesize(self, evidence, research_plan, max_items=10):
        prompt = {
            "task": "Analyze supplied market evidence and produce evidence-backed business opportunities.",
            "research_plan": research_plan,
            "evidence": evidence[:80],
            "requirements": [
                "Identify repeated painful problems.",
                "Do not invent evidence not present in the supplied records.",
                "Return opportunities with explicit customer, problem, solution, revenue model, and evidence.",
                "Favor fast validation, automation, healthy margins, recurring revenue, and capital efficiency.",
                "Return JSON files contract only because this adapter uses the shared resilient provider contract.",
            ],
            "note": (
                "For compatibility with the shared coding-provider transport, place a JSON document "
                "containing an 'opportunities' array inside files['opportunities.json']."
            ),
            "max_items": int(max_items),
        }
        result = self.adapter.generate(prompt)
        if not result.get("success"):
            return {"success": False, "reason": result.get("reason"), "opportunities": []}

        raw = result.get("files", {}).get("opportunities.json")
        if not raw:
            return {"success": False, "reason": "opportunities_json_missing", "opportunities": []}

        try:
            data = json.loads(raw)
            opportunities = data.get("opportunities", [])
            if not isinstance(opportunities, list):
                opportunities = []
            return {
                "success": True,
                "opportunities": opportunities[:int(max_items)],
                "model": result.get("model"),
            }
        except Exception as exc:
            return {
                "success": False,
                "reason": f"opportunity_parse_failed:{type(exc).__name__}",
                "opportunities": [],
            }
