class PortfolioSnapshot:
    """442: CEO-readable portfolio summary."""

    def build(self, ventures):
        counts = {}
        for v in ventures:
            counts[v.get("status","unknown")] = counts.get(v.get("status","unknown"),0) + 1
        return {
            "venture_count":len(ventures),
            "status_counts":counts,
            "top_priorities":[
                {
                    "venture_id":v.get("venture_id"),
                    "name":v.get("name"),
                    "priority":v.get("priority"),
                    "status":v.get("status"),
                }
                for v in sorted(ventures, key=lambda x: float(x.get("priority",0)), reverse=True)[:5]
            ]
        }
