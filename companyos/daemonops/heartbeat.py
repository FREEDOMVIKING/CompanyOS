class HeartbeatMonitor:
    def evaluate(self, heartbeats, now_tick):
        rows=[]
        for h in heartbeats or []:
            age=int(now_tick)-int(h.get("last_tick",0))
            rows.append({
                "worker":h.get("worker"),
                "age_ticks":age,
                "healthy":age <= int(h.get("max_age_ticks",3))
            })
        return rows
