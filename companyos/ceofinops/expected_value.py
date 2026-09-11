class ExpectedValueEngine:
    def evaluate(self, plan):
        capital = float(plan.get("required_capital", 0) or 0)
        gross_return = float(plan.get("expected_return", 0) or 0)
        confidence = float(plan.get("confidence", 0.5) or 0.5)
        risk = float(plan.get("risk", 0.5) or 0.5)

        expected_gain = gross_return * confidence
        risk_adjustment = capital * risk
        net_expected_value = expected_gain - risk_adjustment

        return {
            "expected_gain": round(expected_gain, 8),
            "risk_adjustment": round(risk_adjustment, 8),
            "net_expected_value": round(net_expected_value, 8),
            "positive_ev": net_expected_value > 0,
        }
