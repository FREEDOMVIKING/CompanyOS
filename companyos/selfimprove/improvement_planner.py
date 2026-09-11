class ImprovementPlanner:
    def plan(self, bottlenecks):
        actions=[]
        for b in bottlenecks or []:
            action={
                "reliability":"improve_retry_and_verification",
                "latency":"optimize_routing_and_parallelism",
                "cost":"reduce_expensive_provider_usage",
                "recovery":"strengthen_checkpoint_and_failover"
            }.get(b.get("kind"),"investigate")
            actions.append({**b,"improvement_action":action})
        return actions
