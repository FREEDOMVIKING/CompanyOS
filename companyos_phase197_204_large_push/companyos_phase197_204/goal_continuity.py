class GoalContinuityEngine:
    """197: keep durable objectives alive across autonomous cycles."""
    def reconcile(self, goals, results):
        completed={str(x.get("goal")) for x in results if x.get("success")}
        out=[]
        for g in goals:
            name=str(g.get("goal"))
            if name not in completed:
                out.append({**g,"status":"active","carry_forward":True,"autonomous":True})
        return out
