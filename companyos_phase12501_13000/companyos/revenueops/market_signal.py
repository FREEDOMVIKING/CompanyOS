class MarketSignalEngine:
    def rank(self, signals):
        out=[]
        for s in signals or []:
            score=(float(s.get("demand",0))*.35+float(s.get("urgency",0))*.25+
                   float(s.get("willingness_to_pay",0))*.25+float(s.get("fit",0))*.15)
            out.append({**s,"signal_score":round(score,4)})
        return sorted(out,key=lambda x:x["signal_score"],reverse=True)
