class RetentionAction:
    """645: recommend bounded retention interventions."""

    def recommend(self, risk):
        reasons=set(risk.get("reasons",[]))
        actions=[]
        if "support_friction" in reasons: actions.append("resolve_high_impact_support_issues")
        if "usage_decline" in reasons: actions.append("investigate_activation_or_value_gap")
        if "low_customer_health" in reasons: actions.append("customer_success_review")
        if "cancellation_intent" in reasons: actions.append("capture_churn_reason_and_offer_relevant_help")
        if "payment_risk" in reasons: actions.append("review_billing_issue")
        if not actions: actions.append("continue_monitoring")
        return {"actions":actions,"automatic_financial_concession":False}
