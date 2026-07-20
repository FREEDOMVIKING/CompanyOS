class MarketFeedbackLoop:
    """150: convert observed feedback into evidence-weighted next actions."""
    def analyze(self, signals):
        out=[]
        for s in signals:
            strength=float(s.get("strength",0)); confidence=float(s.get("confidence",0))
            score=strength*confidence
            action="double_down" if score>=.65 else "iterate" if score>=.3 else "revalidate"
            out.append({**s,"evidence_score":round(score,4),"next_action":action})
        return sorted(out,key=lambda x:x["evidence_score"],reverse=True)
