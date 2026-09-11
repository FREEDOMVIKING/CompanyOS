import os

class BuildBudget:
    """408: bounded MVP build budget."""

    def limits(self):
        return {
            "max_build_cycles": max(1, int(os.getenv("COMPANYOS_MAX_MVP_BUILD_CYCLES", "8"))),
            "max_repair_cycles": max(1, int(os.getenv("COMPANYOS_MAX_MVP_REPAIR_CYCLES", "4"))),
            "max_scope_growth_percent": max(0, int(os.getenv("COMPANYOS_MAX_SCOPE_GROWTH_PERCENT", "20"))),
            "external_spend_requires_policy_approval": True,
        }
