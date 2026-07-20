class DelegationDirector:
    """159: delegate missions to specialist agents with autonomous handoffs."""
    def delegate(self,tasks,agents):
        result=[]
        for t in tasks:
            req=set(t.get("capabilities",[])); best=None; bestscore=-1e9
            for a in agents:
                score=len(req & set(a.get("capabilities",[])))*10+float(a.get("reliability",0))-float(a.get("load",0))
                if score>bestscore: bestscore,best=score,a
            result.append({**t,"agent":best.get("name") if best else None,"autonomous_handoff":True})
        return result
