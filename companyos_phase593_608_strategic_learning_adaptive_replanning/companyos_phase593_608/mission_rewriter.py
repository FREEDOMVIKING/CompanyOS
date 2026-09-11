class MissionRewriter:
    """598: rewrite the next mission around new strategy."""

    def rewrite(self, mission, strategy):
        mission = dict(mission or {})
        context = dict(mission.get("context") or {})
        context["strategy_adjustments"] = strategy.get("changes",[])
        mission["context"] = context

        changes = strategy.get("changes",[])
        if "revisit_problem_solution_fit" in changes:
            mission["mission_type"] = "research"
            mission["priority"] = max(float(mission.get("priority",0.5)),0.9)
        elif "increase_test_and_repair_emphasis" in changes and mission.get("mission_type") == "build":
            mission["priority"] = 1.0
        elif "retest_offer_pricing_or_customer_segment" in changes:
            mission["mission_type"] = "validation"
            mission["priority"] = 1.0

        return mission
