class ServiceSupervisor:
    """193: supervise internal services and autonomously recover routine faults."""
    def inspect(self,services):
        actions=[]
        for s in services:
            if s.get("healthy",True): continue
            failures=int(s.get("consecutive_failures",1))
            action="restart" if failures<3 else "failover" if s.get("fallback") else "isolate"
            actions.append({"service":s.get("name"),"action":action,"autonomous":True,"verify_after":True})
        return actions
