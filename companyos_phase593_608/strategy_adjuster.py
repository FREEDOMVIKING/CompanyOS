class StrategyAdjuster:
    """597: convert lessons into strategy adjustments."""

    def adjust(self, current, lessons):
        strategy = dict(current or {})
        strategy.setdefault("focus","current_plan")
        strategy.setdefault("changes",[])

        if "mission_execution_failed" in lessons:
            strategy["changes"].append("reduce_scope_or_change_execution_path")
        if "quality_failure" in lessons:
            strategy["changes"].append("increase_test_and_repair_emphasis")
        if "weak_activation" in lessons:
            strategy["changes"].append("improve_onboarding_and_time_to_value")
        if "weak_retention" in lessons:
            strategy["changes"].append("revisit_problem_solution_fit")
        if "no_revenue_signal" in lessons:
            strategy["changes"].append("retest_offer_pricing_or_customer_segment")
        if any(x.startswith("stage_advanced:") for x in lessons):
            strategy["changes"].append("preserve_working_strategy_elements")

        strategy["changes"] = list(dict.fromkeys(strategy["changes"]))
        return strategy
