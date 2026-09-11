class ExpansionRadar:
    def rank(self, opportunities):
        rows=[]
        for o in opportunities or []:
            demand=float(o.get("demand",0))
            fit=float(o.get("strategic_fit",0))
            margin=float(o.get("margin_potential",0))
            speed=float(o.get("speed_to_market",0))
            risk=float(o.get("risk",0))
            score=demand*.3+fit*.25+margin*.2+speed*.15+(1-risk)*.1
            rows.append({**o,"expansion_score":round(score,4)})
        return sorted(rows,key=lambda x:x["expansion_score"],reverse=True)
