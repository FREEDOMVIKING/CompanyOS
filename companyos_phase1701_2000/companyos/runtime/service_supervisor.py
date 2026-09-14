class ServiceSupervisor:
    def evaluate(self, services):
        actions=[]
        for s in services or []:
            if not s.get("healthy",False):
                actions.append({"service":s.get("service"),"action":"restart"})
            else:
                actions.append({"service":s.get("service"),"action":"keep_running"})
        return actions
