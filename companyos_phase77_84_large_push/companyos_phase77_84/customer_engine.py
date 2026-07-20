class CustomerEngine:
    """77: segment customers and prioritize pain/value signals."""
    def segment(self, signals):
        groups={}
        for s in signals:
            seg=str(s.get("segment","unknown"))
            g=groups.setdefault(seg,{"count":0,"pain":0.0,"willingness":0.0})
            g["count"]+=1; g["pain"]+=float(s.get("pain",0)); g["willingness"]+=float(s.get("willingness",0))
        out=[]
        for name,g in groups.items():
            n=g["count"]; pain=g["pain"]/n; willingness=g["willingness"]/n
            out.append({"segment":name,"count":n,"pain":round(pain,4),"willingness":round(willingness,4),
                        "priority":round(pain*.55+willingness*.45,4)})
        return sorted(out,key=lambda x:x["priority"],reverse=True)
