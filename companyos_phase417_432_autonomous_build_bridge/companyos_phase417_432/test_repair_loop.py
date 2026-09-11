class TestRepairLoop:
    """421: deterministic repair policy around test results."""

    def evaluate(self, test_result, repair_cycle, max_repairs):
        passed = bool(test_result.get("passed"))
        if passed:
            return {"action":"promote","reason":"tests_passed"}
        if repair_cycle < max_repairs:
            return {"action":"repair","reason":"tests_failed_repair_budget_available"}
        return {"action":"halt","reason":"repair_budget_exhausted"}
