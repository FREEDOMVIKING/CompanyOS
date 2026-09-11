class MarketEntryPlanner:
    def plan(self, opportunity):
        return {
            "opportunity":opportunity,
            "steps":[
                "validate_local_demand",
                "confirm_compliance_requirements",
                "adapt_offer",
                "establish_distribution",
                "launch_small_pilot",
                "measure_unit_economics",
                "scale_if_validated"
            ]
        }
