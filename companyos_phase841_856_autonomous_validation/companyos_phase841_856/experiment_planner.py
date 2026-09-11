class ExperimentPlanner:
    """843: generate bounded validation experiments."""
    def plan(self, hypotheses):
        plans=[]
        for h in (hypotheses or {}).get("hypotheses",[]):
            t=h.get("type")
            if t=="problem":
                method="customer_interviews"
            elif t=="demand":
                method="landing_page_or_outreach"
            elif t=="pricing":
                method="pricing_test"
            else:
                method="evidence_review"
            plans.append({
                "hypothesis_type":t,
                "method":method,
                "success_metric":"clear positive signal",
                "max_cost_usd":50,
                "external_action_required":False,
            })
        return plans
