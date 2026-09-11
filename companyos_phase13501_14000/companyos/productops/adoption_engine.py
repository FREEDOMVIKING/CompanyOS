class AdoptionEngine:
    def analyze(self, cohorts):
        rows=[]
        for c in cohorts or []:
            activation=float(c.get("activation",0))
            engagement=float(c.get("engagement",0))
            retention=float(c.get("retention",0))
            score=activation*.35+engagement*.3+retention*.35
            action="scale_onboarding" if score>=.8 else ("improve_activation" if activation<.6 else "improve_retention")
            rows.append({**c,"adoption_score":round(score,4),"action":action})
        return rows
