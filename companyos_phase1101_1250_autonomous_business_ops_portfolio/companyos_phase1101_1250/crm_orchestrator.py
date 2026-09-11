class CRMOrchestrator:
    """1151-1160: next-best-action workflow for leads/customers."""
    def actions(self, records):
        actions=[]
        for r in records or []:
            kind=r.get("kind","lead")
            if kind=="lead":
                if r.get("stage")=="proposal":
                    action="follow_up_proposal"
                elif r.get("score",0)>=60:
                    action="schedule_demo"
                else:
                    action="nurture"
            else:
                if r.get("health_score",1)<0.5:
                    action="customer_success_outreach"
                elif r.get("expansion_signal"):
                    action="expansion_offer"
                else:
                    action="monitor"
            actions.append({"id":r.get("id"),"action":action})
        return actions
