class BuildTestFixLoop:
    """977-984: bounded build/test/fix execution controller."""
    def run(self, build_result=None, test_results=None, max_fix_rounds=3):
        build_result = dict(build_result or {"success":True})
        tests = list(test_results or [])
        failures = [t for t in tests if not t.get("passed",False)]
        rounds = 0
        while failures and rounds < int(max_fix_rounds):
            rounds += 1
            for f in failures:
                f["fix_attempted"] = True
                f["passed"] = bool(f.get("fixable",True))
            failures = [t for t in failures if not t.get("passed",False)]
        return {
            "build_success": bool(build_result.get("success")),
            "tests_passed": len(failures)==0,
            "fix_rounds": rounds,
            "remaining_failures": failures,
        }
