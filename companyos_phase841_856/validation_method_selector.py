class ValidationMethodSelector:
    """844: select methods based on hypothesis type and available evidence."""
    def select(self, hypothesis_type, evidence_count=0):
        if hypothesis_type=="problem":
            return "customer_interviews" if evidence_count < 5 else "evidence_review_plus_interviews"
        if hypothesis_type=="demand":
            return "landing_page_or_outreach"
        if hypothesis_type=="pricing":
            return "pricing_test"
        return "evidence_review"
