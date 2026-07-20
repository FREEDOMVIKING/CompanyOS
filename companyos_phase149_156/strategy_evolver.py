class StrategyEvolver:
    """155: evolve strategy from measurable evidence."""
    def evolve(self, strategies):
        rows=[]
        for s in strategies:
            score=float(s.get("results",0))*.45+float(s.get("learning",0))*.25+float(s.get("repeatability",0))*.2-float(s.get("risk",0))*.1
            decision="expand" if score>=.7 else "refine" if score>=.4 else "replace"
            rows.append({**s,"strategy_score":round(score,4),"decision":decision})
        return sorted(rows,key=lambda x:x["strategy_score"],reverse=True)
