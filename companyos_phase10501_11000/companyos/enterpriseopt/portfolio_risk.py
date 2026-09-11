class PortfolioRiskEngine:
    def evaluate(self, ventures):
        concentration={}
        for v in ventures or []:
            sector=v.get("sector","unknown")
            concentration[sector]=concentration.get(sector,0)+float(v.get("capital",0))
        total=sum(concentration.values()) or 1
        ratios={k:round(v/total,3) for k,v in concentration.items()}
        max_ratio=max(ratios.values()) if ratios else 0
        return {
            "concentration":ratios,
            "high_concentration":max_ratio>.6,
            "max_concentration":max_ratio
        }
