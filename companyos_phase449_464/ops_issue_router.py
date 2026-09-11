class OpsIssueRouter:
    """459: route operational issues to the right specialist."""

    def route(self, issue):
        category = str(issue.get("category","")).lower()
        if category in ("bug","reliability","security"):
            role = "engineering"
        elif category in ("support","customer"):
            role = "customer_success"
        elif category in ("pricing","growth","conversion"):
            role = "growth"
        elif category in ("billing","revenue","finance"):
            role = "finance_ops"
        else:
            role = "operations"
        return {**issue, "assigned_role":role}
