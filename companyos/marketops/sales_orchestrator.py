class SalesOrchestrator:
    def next_actions(self, leads):
        out=[]
        for lead in leads or []:
            score=(
                (25 if lead.get("pain_confirmed") else 0)+
                (25 if lead.get("budget_confirmed") else 0)+
                (20 if lead.get("authority_confirmed") else 0)+
                (20 if lead.get("timeline_confirmed") else 0)+
                min(10,int(float(lead.get("engagement",0))*10))
            )
            if score>=80: action="proposal"
            elif score>=60: action="demo"
            elif score>=40: action="qualify"
            else: action="nurture"
            out.append({**lead,"lead_score":score,"next_action":action})
        return out
