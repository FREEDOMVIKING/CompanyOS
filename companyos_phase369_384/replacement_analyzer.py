from __future__ import annotations

class ReplacementAnalyzer:
    """376: identify current alternatives and replacement friction."""

    def analyze(self, cluster):
        text = " ".join(str(r.get("text","")) for r in cluster.get("records", [])).lower()
        alternatives = []
        if "spreadsheet" in text or "excel" in text:
            alternatives.append("spreadsheets")
        if "manual" in text:
            alternatives.append("manual process")
        if "subscription" in text or "software" in text:
            alternatives.append("existing software")
        return {
            "current_alternatives": alternatives or ["unknown / requires validation"],
            "replacement_opportunity": bool(alternatives),
        }
