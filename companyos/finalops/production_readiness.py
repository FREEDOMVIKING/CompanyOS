class ProductionReadiness:
    def score(self, inventory, integrations, e2e, regression, continuity, recovery, approvals):
        checks={
            "inventory":bool(inventory.get("complete")),
            "integrations":bool(integrations.get("valid")),
            "end_to_end":bool(e2e.get("passed")),
            "regression":bool(regression.get("passed")),
            "continuity":bool(continuity.get("continuous")),
            "recovery":bool(recovery.get("passed")),
            "approval_boundaries":bool(approvals.get("passed"))
        }
        score=sum(1 for v in checks.values() if v)/len(checks)
        return {"score":round(score,3),"ready":all(checks.values()),"checks":checks}
