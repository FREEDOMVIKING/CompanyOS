from datetime import datetime, timezone, timedelta
from .util import stable_id, now

class Scheduler:
    def __init__(self, db):
        self.db=db

    def ensure_defaults(self):
        self.db.upsert_schedule("health-60","System health refresh",60,"system_health","recovery",90,{})
        self.db.upsert_schedule("portfolio-120","Portfolio review",120,"portfolio_review","ceo",80,{})
        self.db.upsert_schedule("plugins-180","Plugin health",180,"plugin_health","recovery",70,{})

    def enqueue_due(self, context):
        current=datetime.now(timezone.utc)
        created=0
        for s in self.db.list_schedules():
            if not s.get("enabled"): continue
            next_run=s.get("next_run_at")
            due=True
            if next_run:
                try: due=datetime.fromisoformat(next_run) <= current
                except Exception: due=True
            if not due: continue
            payload=dict(s.get("payload",{}))
            payload.update(context)
            bucket=int(current.timestamp() // max(1,int(s["cadence_seconds"])))
            tid=stable_id("scheduled",s["schedule_id"],bucket)
            self.db.add_task(tid,s["task_kind"],s["name"],s["priority"],s["agent"],payload)
            nr=current+timedelta(seconds=int(s["cadence_seconds"]))
            self.db.mark_schedule_run(s["schedule_id"],now(),nr.isoformat())
            created+=1
        return created
