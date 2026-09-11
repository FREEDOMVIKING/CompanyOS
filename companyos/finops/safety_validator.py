class FinancialSafetyValidator:
    def validate(self, simulation_result):
        result = simulation_result or {}
        status = result.get("status")

        checks = {
            "simulation_completed": bool(result),
            "treasury_not_blocked": status != "treasury_blocked",
            "no_live_execution": status != "executed",
            "idempotency_present": bool(result.get("idempotency_key")),
            "acceptable_resolution": status in {
                "dry_run_authorized",
                "approval_required",
                "treasury_blocked",
                "signing_authorization_required",
                "idempotent_replay",
            }
        }

        return {
            "passed": all(checks.values()),
            "checks": checks,
            "status": status
        }
