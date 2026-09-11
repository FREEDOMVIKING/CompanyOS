class AcquisitionScore:
    """632: score acquisition quality rather than raw traffic."""

    def score(self, funnel, vanity):
        score=0.0
        score += min(3.0,float(funnel.get("visitor_to_lead",0))*10)
        score += min(2.0,float(funnel.get("lead_to_activation",0))*5)
        score += min(3.0,float(funnel.get("activation_to_paid",0))*8)
        score += min(2.0,float(funnel.get("paid_to_retained",0))*4)
        if vanity.get("vanity_only"):
            score=min(score,1.0)
        return round(score,2)
