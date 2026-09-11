class ToolRouter:
    def route(self, task, integrations):
        cap=task.get("capability")
        candidates=[x for x in integrations if x.get("enabled") and (not cap or cap in x.get("capabilities",[]))]
        candidates=sorted(candidates,key=lambda x:float((x.get("metadata") or {}).get("priority",0.5)),reverse=True)
        return {"task":task,"candidates":candidates,"selected":candidates[0] if candidates else None}
