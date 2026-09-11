class LongRunningServiceSupervisor:
    def evaluate(self, services):
        actions=[]
        for s in services or []:
            if not s.get("healthy",False):
                actions.append({"service":s.get("service"),"action":"restart","reason":s.get("reason","unhealthy")})
            elif float(s.get("load",0))>0.9:
                actions.append({"service":s.get("service"),"action":"scale_downstream_pressure"})
            else:
                actions.append({"service":s.get("service"),"action":"keep_running"})
        return actions
