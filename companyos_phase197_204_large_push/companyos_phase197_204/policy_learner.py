class PolicyLearner:
    """201: promote repeated successful internal behaviors into learned defaults."""
    def learn(self,behaviors):
        out=[]
        for b in behaviors:
            runs=int(b.get("runs",0)); success=float(b.get("success_rate",0)); improvement=float(b.get("improvement",0))
            promote=runs>=4 and success>=.75 and improvement>0
            out.append({**b,"promote":promote,"learned_default":promote})
        return out
