class KPIEngine:
    """1205-1216: unify venture KPIs into operating scorecard."""
    def score(self, metrics):
        m=metrics or {}
        revenue=float(m.get("revenue_growth",0))
        retention=float(m.get("retention_rate",0))
        margin=float(m.get("gross_margin",0))
        conversion=float(m.get("conversion_rate",0))
        reliability=float(m.get("reliability",1))
        score=revenue*0.25+retention*0.25+margin*0.2+conversion*0.15+reliability*0.15
        return {
            "score":round(max(0,min(1,score)),3),
            "signals":{
                "revenue_growth":revenue,
                "retention_rate":retention,
                "gross_margin":margin,
                "conversion_rate":conversion,
                "reliability":reliability,
            }
        }
