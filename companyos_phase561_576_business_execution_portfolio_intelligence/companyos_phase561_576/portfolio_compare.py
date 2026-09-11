class PortfolioCompare:
    """567: rank ventures using comparable scorecards."""

    def rank(self, ventures):
        return sorted(
            ventures,
            key=lambda v: (
                float(v.get("score",0)),
                float(v.get("revenue_signal",0)),
                float(v.get("retention_rate",0)),
            ),
            reverse=True,
        )
