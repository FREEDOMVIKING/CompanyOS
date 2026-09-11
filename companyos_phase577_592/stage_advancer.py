class StageAdvancer:
    """581: advance only when stage-specific evidence is present."""

    ORDER = ["research","validation","build","launch","operations","scale"]

    def next_stage(self, current, evidence):
        current = current if current in self.ORDER else "research"

        if current == "research":
            return "validation" if evidence.get("validation_candidate_ready") else "research"
        if current == "validation":
            return "build" if evidence.get("validation_decision") in ("go_to_mvp","approved_for_mvp","validated") else "validation"
        if current == "build":
            return "launch" if evidence.get("release_candidate_ready") and evidence.get("tests_passed") else "build"
        if current == "launch":
            return "operations" if evidence.get("controlled_launch_complete") else "launch"
        if current == "operations":
            if float(evidence.get("retention_rate",0)) >= 0.3 and float(evidence.get("revenue_signal",0)) >= 3:
                return "scale"
            return "operations"
        return "scale"
