class ProductionObservability:
    def snapshot(self, services, missions, approvals, recovery):
        healthy=sum(1 for s in services or [] if s.get("healthy"))
        total=len(services or [])
        return {
            "service_health_ratio":round(healthy/max(1,total),3),
            "mission_count":len(missions or []),
            "pending_approvals":approvals.get("pending_count",0),
            "recovery_actions":len(recovery.get("actions",[])),
            "healthy":healthy==total and recovery.get("recoverable",True)
        }
