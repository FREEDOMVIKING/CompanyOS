class VentureEngine:
    def select(self, candidates):
        ranked = []
        for c in candidates or []:
            value = float(c.get("expected_value", 0) or 0)
            confidence = float(c.get("confidence", 0.5) or 0.5)
            risk = float(c.get("risk", 0.5) or 0.5)
            effort = float(c.get("effort", 0.5) or 0.5)
            score = value * confidence * (1-risk) * (1-effort/2)
            row = dict(c)
            row["venture_score"] = round(score, 8)
            ranked.append(row)
        return sorted(ranked, key=lambda x: x["venture_score"], reverse=True)
