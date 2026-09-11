class SupportTriage:
    """642: prioritize customer support issues by severity and business impact."""

    WEIGHTS={"critical":100,"high":70,"medium":40,"low":10}

    def prioritize(self, tickets):
        ranked=[]
        for t in tickets or []:
            severity=str(t.get("severity","low")).lower()
            score=self.WEIGHTS.get(severity,10)
            score += 20 if t.get("blocks_core_value") else 0
            score += 10 if t.get("multiple_customers_affected") else 0
            ranked.append({**t,"priority_score":score})
        return sorted(ranked,key=lambda x:x["priority_score"],reverse=True)
