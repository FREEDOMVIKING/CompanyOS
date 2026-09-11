class CrossSystemScheduler:
    def schedule(self, work_items, capability_registry):
        out=[]
        for item in work_items or []:
            cap=item.get("capability")
            candidates=capability_registry.get(cap,[])
            candidates=sorted(
                candidates,
                key=lambda x:float(x.get("health",0))*0.6+float(x.get("capacity",0))*0.4,
                reverse=True
            )
            out.append({
                **item,
                "selected_system":candidates[0]["system"] if candidates else None,
                "status":"scheduled" if candidates else "capability_gap"
            })
        return out
