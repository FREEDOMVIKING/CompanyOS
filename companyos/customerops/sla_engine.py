class SLAEngine:
    def evaluate(self, tickets):
        breaches=[]
        for t in tickets or []:
            target=float(t.get("sla_minutes",60)); elapsed=float(t.get("elapsed_minutes",0))
            if elapsed>target: breaches.append({"ticket_id":t.get("ticket_id"),"over_minutes":round(elapsed-target,2)})
        return {"breaches":breaches,"sla_ok":not breaches}
