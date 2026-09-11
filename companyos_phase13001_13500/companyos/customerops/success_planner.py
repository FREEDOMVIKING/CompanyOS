class CustomerSuccessPlanner:
    def plan(self, customer):
        score=float(customer.get("health_score",0))
        if score<.5: actions=["diagnose_root_cause","restore_value","human_review_if_needed"]
        elif score<.75: actions=["proactive_checkin_plan","increase_adoption","measure_outcome"]
        else: actions=["document_success","identify_expansion_fit","maintain_value"]
        return {"customer_id":customer.get("customer_id"),"actions":actions}
