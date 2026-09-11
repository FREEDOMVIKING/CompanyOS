class ProductionSupervisor:
    def evaluate(self, services):
        actions=[]
        for s in services or []:
            healthy=bool(s.get("healthy",False))
            if healthy:
                action="keep_running"
            elif s.get("restartable",True):
                action="restart"
            else:
                action="isolate_and_review"
            actions.append({"service":s.get("service"),"action":action})
        return actions
