class CustomerSignalEngine:
    def aggregate(self, signals):
        pain=[]; requests=[]; objections=[]
        for s in signals or []:
            kind=s.get("kind","unknown")
            if kind=="pain": pain.append(s)
            elif kind=="request": requests.append(s)
            elif kind=="objection": objections.append(s)
        return {"pain_signals":pain,"feature_requests":requests,"objections":objections,"signal_count":len(signals or [])}
