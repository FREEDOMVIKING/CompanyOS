class SelfHealingSupervisor:
    def evaluate(self, workers):
        actions=[]
        for w in workers or []:
            if w.get("healthy",False):
                action="keep_running"
            elif int(w.get("restart_count",0)) < int(w.get("max_restarts",3)):
                action="restart"
            else:
                action="isolate_and_alert"
            actions.append({"worker":w.get("name"),"action":action})
        return actions
