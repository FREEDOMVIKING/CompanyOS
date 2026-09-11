class StageCapabilityRouter:
    DEFAULT_MAP = {
        "discover": ["research", "market_scan", "opportunity_discovery"],
        "research": ["research", "web_research", "analysis"],
        "select": ["ceo", "portfolio_review", "strategy"],
        "plan": ["ceo", "planning", "project_management"],
        "budget": ["finance", "financial_planning", "treasury"],
        "build": ["coding", "engineering", "project_management"],
        "test": ["quality", "engineering", "verification"],
        "launch_review": ["release", "deployment", "marketing"],
        "operate": ["operations", "project_management"],
        "customers": ["customer_success", "communications"],
        "revenue": ["finance", "revenueops"],
        "accounting": ["finance", "accounting"],
        "evaluate": ["analysis", "finance", "research"],
        "portfolio_decision": ["ceo", "portfolio_review", "strategy"],
        "learn": ["research", "analysis", "memory"],
    }

    def candidates(self, stage):
        return list(self.DEFAULT_MAP.get(stage, []))

    def resolve(self, stage, available_capabilities):
        available = set(available_capabilities or [])
        for name in self.candidates(stage):
            if name in available:
                return {"stage": stage, "capability": name, "matched": True}
        return {"stage": stage, "capability": None, "matched": False}
