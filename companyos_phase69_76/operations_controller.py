from typing import Any, Dict
class OperationsController:
    """74: operational health and incident priority."""
    def assess(self, systems:Dict[str,Any]):
        incidents=[]; healthy=0
        for name,state in systems.items():
            ok=bool(state.get("healthy",False)) if isinstance(state,dict) else bool(state)
            if ok: healthy+=1
            else: incidents.append({"system":name,"priority":"high"})
        total=len(systems)
        return {"health":round(healthy/total,4) if total else 1.0,"incidents":incidents,
                "status":"healthy" if not incidents else "attention_required"}
