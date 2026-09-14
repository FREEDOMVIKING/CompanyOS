class AutonomousScheduler:
    def plan(self, cadence):
        cadence=cadence or {}
        jobs=[]
        for name in cadence.get("daily",[]):
            jobs.append({"task_type":"daily_cycle","name":name,"priority":7})
        for name in cadence.get("weekly",[]):
            jobs.append({"task_type":"weekly_cycle","name":name,"priority":5})
        for name in cadence.get("monthly",[]):
            jobs.append({"task_type":"monthly_cycle","name":name,"priority":3})
        return jobs
