class ResultInterpreter:
    """394: compare observed validation metrics against thresholds."""

    def interpret(self, metrics, thresholds):
        checks = {}
        mapping = {
            "landing_page_visits": ("landing_page_visit_min", lambda a,b: a >= b),
            "email_conversion": ("email_conversion_min", lambda a,b: a >= b),
            "interview_count": ("interview_count_min", lambda a,b: a >= b),
            "pain_confirm_rate": ("pain_confirm_rate_min", lambda a,b: a >= b),
            "willingness_to_pay_confirm_rate": ("willingness_to_pay_confirm_rate_min", lambda a,b: a >= b),
            "qualified_leads": ("qualified_leads_min", lambda a,b: a >= b),
        }
        for key, (threshold_key, fn) in mapping.items():
            if key in metrics:
                checks[key] = {
                    "value": metrics[key],
                    "threshold": thresholds[threshold_key],
                    "passed": fn(metrics[key], thresholds[threshold_key]),
                }
        passed = sum(1 for x in checks.values() if x["passed"])
        return {
            "checks": checks,
            "passed_checks": passed,
            "total_checks": len(checks),
            "pass_ratio": (passed / len(checks)) if checks else 0.0,
        }
