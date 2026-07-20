class InitiativeSpawner:
    """198: spawn new internal initiatives when active goals lack sufficient work."""
    def spawn(self, goals, active_tasks):
        covered={str(t.get("goal")) for t in active_tasks}
        return [{"goal":g.get("goal"),"initiative":f"advance:{g.get('goal')}",
                 "status":"queued","autonomous":True}
                for g in goals if str(g.get("goal")) not in covered]
