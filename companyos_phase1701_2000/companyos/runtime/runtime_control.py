class UnifiedRuntimeControl:
    def commands(self):
        return ["start","stop","status","health","cycle","recover"]

    def status(self, queue_snapshot, heartbeat, watchdog):
        return {
            "queue":queue_snapshot,
            "heartbeat":heartbeat,
            "watchdog":watchdog,
            "running":bool(watchdog.get("healthy")),
        }
