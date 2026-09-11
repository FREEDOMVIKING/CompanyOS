class CustomerDiscoveryEngine:
    def segment(self, prospects):
        buckets={}
        for p in prospects or []:
            seg=p.get("segment","unknown")
            buckets.setdefault(seg,[]).append(p)
        ranked=[]
        for seg, rows in buckets.items():
            pain=sum(float(x.get("pain",0)) for x in rows)/max(1,len(rows))
            budget=sum(float(x.get("budget_signal",0)) for x in rows)/max(1,len(rows))
            urgency=sum(float(x.get("urgency",0)) for x in rows)/max(1,len(rows))
            ranked.append({
                "segment":seg,
                "count":len(rows),
                "score":round(pain*0.4+budget*0.35+urgency*0.25,3)
            })
        return sorted(ranked,key=lambda x:x["score"],reverse=True)
