class CompetitorIntelligence:
    def analyze(self, competitors):
        out=[]
        for c in competitors or []:
            strength=float(c.get("strength",0)); momentum=float(c.get("momentum",0))
            differentiation=float(c.get("differentiation_gap",0))
            out.append({**c,"threat_score":round(strength*.45+momentum*.35+(1-differentiation)*.2,3)})
        return sorted(out,key=lambda x:x["threat_score"],reverse=True)
