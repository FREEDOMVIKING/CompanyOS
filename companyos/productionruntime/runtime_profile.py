class RuntimeProfile:
    def build(self, mode="continuous", max_parallel=8, retry_limit=4, cycle_interval_seconds=300):
        return {
            "mode":mode,
            "max_parallel":int(max_parallel),
            "retry_limit":int(retry_limit),
            "cycle_interval_seconds":int(cycle_interval_seconds),
            "persistent":True,
            "restart_safe":True
        }
