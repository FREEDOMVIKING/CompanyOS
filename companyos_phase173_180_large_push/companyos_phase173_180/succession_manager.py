class SuccessionManager:
    """179: fail over internal responsibilities when an agent becomes unavailable."""
    def reassign(self, responsibilities, agents):
        healthy=[a for a in agents if a.get("healthy",True)]
        result=[]
        for r in responsibilities:
            current=r.get("agent")
            current_ok=any(a.get("name")==current for a in healthy)
            if current_ok:
                result.append({**r,"reassigned":False})
                continue
            candidates=sorted(healthy,key=lambda a:float(a.get("reliability",0))-float(a.get("load",0)),reverse=True)
            result.append({**r,"agent":candidates[0].get("name") if candidates else None,"reassigned":True,"autonomous":True})
        return result
