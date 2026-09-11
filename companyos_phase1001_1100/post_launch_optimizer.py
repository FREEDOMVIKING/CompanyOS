class PostLaunchOptimizer:
    """1069-1076: generate prioritized optimization backlog from product signals."""
    def plan(self, health, growth, feedback):
        backlog=[]
        if not health.get("healthy",True):
            backlog.append({"priority":1,"action":"stabilize_reliability"})
        if float(growth.get("retention_rate",0))<0.4:
            backlog.append({"priority":2,"action":"improve_retention"})
        if float(growth.get("conversion_rate",0))<0.05:
            backlog.append({"priority":3,"action":"improve_conversion"})
        if feedback.get("top_theme"):
            backlog.append({"priority":4,"action":f"address_feedback:{feedback['top_theme']}"})
        return sorted(backlog,key=lambda x:x["priority"])
