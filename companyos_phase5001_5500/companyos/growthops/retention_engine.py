class RetentionEngine:
    def evaluate(self, cohorts):
        out=[]
        for c in cohorts or []:
            retention=float(c.get("retention",0)); expansion=float(c.get("expansion",0))
            satisfaction=float(c.get("satisfaction",0))
            score=retention*.5+expansion*.2+satisfaction*.3
            action="expand" if score>=.75 else ("improve" if score>=.5 else "intervene")
            out.append({**c,"retention_score":round(score,3),"action":action})
        return out
