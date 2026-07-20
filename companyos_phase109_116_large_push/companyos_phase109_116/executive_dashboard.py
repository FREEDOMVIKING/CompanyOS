class ExecutiveDashboard:
    """115: compact executive health summary."""
    def build(self,data):
        return {"missions":data.get("missions",0),"active_tasks":data.get("active_tasks",0),
        "revenue":float(data.get("revenue",0)),"runway_months":data.get("runway_months"),
        "system_health":float(data.get("system_health",0)),"pending_approvals":int(data.get("pending_approvals",0)),
        "critical_alert":float(data.get("system_health",0))<.6 or int(data.get("pending_approvals",0))>10}
