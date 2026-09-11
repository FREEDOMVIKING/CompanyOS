class EvidenceGate:
    """483: explicit evidence-dependent stage gate."""

    def evaluate(self, gate_type, payload):
        payload = payload or {}

        if gate_type == "validation":
            required = [
                "landing_page_visits",
                "email_conversion",
                "interview_count",
                "pain_confirm_rate",
                "willingness_to_pay_confirm_rate",
                "qualified_leads",
            ]
            present = [k for k in required if k in payload]
            ready = len(present) >= 2
        elif gate_type == "operations":
            required = [
                "qualified_visitors",
                "leads",
                "activated_users",
                "paying_customers",
                "sample_size",
            ]
            present = [k for k in required if k in payload]
            ready = len(present) >= 3
        else:
            required = []
            present = []
            ready = True

        return {
            "gate_type":gate_type,
            "ready":ready,
            "required_fields":required,
            "present_fields":present,
            "missing_fields":[k for k in required if k not in payload],
        }
