class RuntimeHealthSnapshot:
    def build(self, queue, watchdog, services, checkpoint):
        healthy=bool(watchdog.get("healthy")) and all(s.get("healthy",False) for s in (services or []))
        return {
            "healthy":healthy,
            "queue":queue,
            "watchdog":watchdog,
            "services":services or [],
            "checkpoint_present":bool(checkpoint),
        }
