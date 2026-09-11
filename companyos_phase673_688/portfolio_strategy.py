class PortfolioStrategy:
    """673: portfolio-level strategy contract."""

    def build(self, objectives=None):
        objectives = objectives or {}
        return {
            "primary_objective": objectives.get("primary","maximize durable portfolio value"),
            "rules":[
                "avoid redundant ventures",
                "favor validated demand and measurable economics",
                "share reusable infrastructure",
                "preserve bounded execution capacity",
                "replace persistently weak ventures with stronger opportunities",
            ],
            "max_active_ventures": int(objectives.get("max_active_ventures",3)),
        }
