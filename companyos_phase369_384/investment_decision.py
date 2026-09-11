from __future__ import annotations

class InvestmentDecision:
    """382: CEO-level go/validate/reject decision."""

    def decide(self, thesis):
        severity = float(thesis.get("pain_severity", 0))
        frequency = float(thesis.get("problem_frequency", 0))
        wtp = float(thesis.get("willingness_to_pay", 0))
        source_count = int((thesis.get("evidence_strength") or {}).get("source_count", 0))

        score = round((severity*0.35 + frequency*0.25 + wtp*0.25 + min(10, source_count*2)*0.15), 2)

        if score >= 7.5 and source_count >= 2:
            action = "priority_validate"
        elif score >= 5.5:
            action = "validate"
        else:
            action = "research_more_or_reject"

        return {"investment_score": score, "decision": action}
