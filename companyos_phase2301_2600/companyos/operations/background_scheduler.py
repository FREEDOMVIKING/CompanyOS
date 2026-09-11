class BackgroundJobScheduler:
    def build(self, daily=None, weekly=None, monthly=None):
        jobs=[]
        for x in daily or []:
            jobs.append({"name":x,"cadence":"daily","priority":8})
        for x in weekly or []:
            jobs.append({"name":x,"cadence":"weekly","priority":5})
        for x in monthly or []:
            jobs.append({"name":x,"cadence":"monthly","priority":3})
        return jobs
