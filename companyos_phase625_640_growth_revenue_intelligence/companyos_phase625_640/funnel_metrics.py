class FunnelMetrics:
    """630: calculate acquisition and conversion funnel."""

    def calculate(self, m):
        visitors=max(1,int(m.get("qualified_visitors",0)))
        leads=int(m.get("qualified_leads",0))
        activated=int(m.get("activated_users",0))
        paying=int(m.get("paying_customers",0))
        retained=int(m.get("retained_customers",0))
        return {
            "visitor_to_lead":round(leads/visitors,4),
            "lead_to_activation":round(activated/max(1,leads),4),
            "activation_to_paid":round(paying/max(1,activated),4),
            "paid_to_retained":round(retained/max(1,paying),4),
            "paying_customers":paying,
            "retained_customers":retained,
        }
