class PriorityEngine:
    def score(self, item):
        value = float(item.get("value", item.get("expected_value", 0.5)) or 0.5)
        confidence = float(item.get("confidence", 0.5) or 0.5)
        urgency = float(item.get("urgency", 0.5) or 0.5)
        risk = float(item.get("risk", 0.3) or 0.3)
        effort = float(item.get("effort", 0.5) or 0.5)
        return round((value*0.35 + confidence*0.2 + urgency*0.2 + (1-risk)*0.15 + (1-effort)*0.1), 6)

    def rank(self, items):
        ranked = []
        for item in items or []:
            row = dict(item)
            row["priority_score"] = self.score(row)
            ranked.append(row)
        return sorted(ranked, key=lambda x: x["priority_score"], reverse=True)
