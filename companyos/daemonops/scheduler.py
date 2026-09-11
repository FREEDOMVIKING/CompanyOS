class AutonomousScheduler:
    def due(self, tasks, tick):
        due=[]
        for t in tasks or []:
            every=max(1, int(t.get("every_ticks",1)))
            if int(tick) % every == 0:
                due.append(t)
        return due
