class IdlePolicy:
    """550: detect low-work conditions and choose idle behavior."""

    def evaluate(self, tick_result):
        sched = (tick_result.get("scheduler_result") or {}).get("scheduler_result") or {}
        executed = int(sched.get("executed_count",0))
        remaining = int(sched.get("remaining_count",0))
        if executed == 0 and remaining == 0:
            return {"idle":True,"reason":"no_ready_work"}
        return {"idle":False,"reason":"work_present"}
