import os

class ValidationBudget:
    """386: cap early validation effort before major build commitment."""

    def limits(self):
        return {
            "max_experiments_per_opportunity": max(1, int(os.getenv("COMPANYOS_MAX_VALIDATION_EXPERIMENTS", "4"))),
            "max_validation_days": max(1, int(os.getenv("COMPANYOS_MAX_VALIDATION_DAYS", "21"))),
            "max_manual_hours": max(1, int(os.getenv("COMPANYOS_MAX_VALIDATION_MANUAL_HOURS", "12"))),
            "default_spend_cap_usd": max(0, float(os.getenv("COMPANYOS_VALIDATION_SPEND_CAP_USD", "0"))),
        }
