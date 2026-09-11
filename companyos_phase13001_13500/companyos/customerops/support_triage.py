class SupportTriageEngine:
    def triage(self, tickets):
        out=[]
        for t in tickets or []:
            severity=float(t.get("severity",0)); impact=float(t.get("impact",0)); blocked=1 if t.get("blocked") else 0
            priority=severity*.45+impact*.4+blocked*.15
            out.append({**t,"priority_score":round(priority,4),"priority":"urgent" if priority>=.8 else ("high" if priority>=.6 else "normal")})
        return sorted(out,key=lambda x:x["priority_score"],reverse=True)
