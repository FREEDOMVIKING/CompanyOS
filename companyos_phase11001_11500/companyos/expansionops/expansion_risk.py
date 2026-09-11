class ExpansionRiskEngine:
    def evaluate(self, opportunity):
        risk=(
            float(opportunity.get("regulatory_risk",0))*.3+
            float(opportunity.get("capital_risk",0))*.25+
            float(opportunity.get("execution_risk",0))*.25+
            float(opportunity.get("demand_uncertainty",0))*.2
        )
        return {
            "risk_score":round(risk,3),
            "risk_level":"high" if risk>=.7 else ("medium" if risk>=.4 else "low")
        }
