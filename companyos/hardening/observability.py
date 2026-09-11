class ObservabilitySnapshot:
    def build(self, health, slos, incidents, capacity):
        return {
            "health":health,
            "slos":slos,
            "incidents":incidents,
            "capacity":capacity,
            "summary":{
                "healthy":bool(health.get("healthy")),
                "all_slos_met":bool(slos.get("all_met")),
                "incident_count":len(incidents or [])
            }
        }
