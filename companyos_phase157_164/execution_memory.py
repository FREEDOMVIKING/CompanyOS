class ExecutionMemory:
    """160: retain outcomes so autonomous cycles learn from prior execution."""
    def summarize(self,runs):
        by={}
        for r in runs:
            k=str(r.get("strategy","unknown")); d=by.setdefault(k,{"runs":0,"wins":0,"score_sum":0.0})
            d["runs"]+=1; d["wins"]+=int(bool(r.get("success"))); d["score_sum"]+=float(r.get("score",0))
        return [{"strategy":k,"runs":v["runs"],"win_rate":round(v["wins"]/v["runs"],4),
                 "average_score":round(v["score_sum"]/v["runs"],4)} for k,v in by.items()]
