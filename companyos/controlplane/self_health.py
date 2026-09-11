class SelfHealthMonitor:
    def evaluate(self, signals):
        s=signals or {}
        queue_ok=int(s.get("queue_backlog",0))<100
        failures_ok=int(s.get("consecutive_failures",0))<3
        heartbeat_ok=bool(s.get("heartbeat_fresh",True))
        memory_ok=not bool(s.get("memory_corruption",False))
        healthy=queue_ok and failures_ok and heartbeat_ok and memory_ok
        actions=[]
        if not queue_ok:actions.append("shed_load")
        if not failures_ok:actions.append("enter_safe_mode")
        if not heartbeat_ok:actions.append("restart_service")
        if not memory_ok:actions.append("restore_checkpoint")
        return {"healthy":healthy,"actions":actions}
