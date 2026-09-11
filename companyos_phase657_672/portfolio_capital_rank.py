class PortfolioCapitalRank:
    """664: rank ventures for bounded resource attention."""

    def rank(self, ventures):
        return sorted(
            ventures,
            key=lambda v: (
                float(v.get("roi_score",0)),
                float(v.get("resource_efficiency",0)),
                float(v.get("revenue_signal",0)),
            ),
            reverse=True,
        )
