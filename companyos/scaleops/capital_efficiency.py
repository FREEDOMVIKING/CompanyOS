class CapitalEfficiencyEngine:
    def evaluate(self, revenue_growth, burn, gross_margin):
        growth=float(revenue_growth)
        burn=max(.01,float(burn))
        margin=float(gross_margin)
        score=growth*0.5+margin*0.35+min(1,1/burn)*0.15
        return {"capital_efficiency_score":round(max(0,min(1,score)),3)}
