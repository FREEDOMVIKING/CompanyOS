class NextActionPolicy:
    """582: select next bounded action from stage and evidence."""

    def decide(self, stage, evidence):
        if stage == "research":
            return "collect_targeted_evidence"
        if stage == "validation":
            return "run_validation"
        if stage == "build":
            return "continue_bounded_build"
        if stage == "launch":
            return "prepare_controlled_launch"
        if stage == "operations":
            if int(evidence.get("critical_issues",0)) > 0:
                return "repair_operational_issues"
            return "measure_and_iterate"
        if stage == "scale":
            return "portfolio_scale_review"
        return "research"
