class StageRouter:
    """467: deterministic CEO lifecycle routing."""

    ORDER = ["opportunity","validation","venture","build","operations","portfolio"]

    def next_stage(self, current, result):
        if not result.get("success"):
            return current

        status = str(result.get("status",""))

        if current == "opportunity":
            return "validation" if "candidate" in status or "opportunity" in status or result.get("data",{}).get("top_thesis") else "opportunity"
        if current == "validation":
            decision = result.get("data",{}).get("decision")
            if isinstance(decision, dict):
                decision = decision.get("decision")
            return "venture" if decision in ("go_to_mvp","approved_for_mvp","validated") else "opportunity"
        if current == "venture":
            return "build"
        if current == "build":
            return "operations" if result.get("data",{}).get("release_candidate_ready") else "build"
        if current == "operations":
            return "portfolio"
        if current == "portfolio":
            decision = result.get("data",{}).get("decision")
            return "operations" if decision in ("scale","iterate","hold_for_more_evidence") else "opportunity"
        return "opportunity"
