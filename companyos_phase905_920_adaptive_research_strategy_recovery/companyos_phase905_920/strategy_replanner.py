class StrategyReplanner:
    """906: convert stagnation causes into a revised research strategy."""
    def build(self, causes):
        causes=set((causes or {}).get("reasons",[]))
        actions=[]
        if "weak_problem_evidence" in causes:
            actions.append("target_direct_customer_pain_sources")
        if "weak_pricing_evidence" in causes:
            actions.append("target_purchase_intent_and_budget_sources")
        if "low_source_diversity" in causes:
            actions.append("force_new_source_classes")
        if "confidence_stagnation" in causes:
            actions.append("change_query_and_provider_mix")
        return {"actions":actions or ["broaden_research_strategy"],"strategy_version":2}
