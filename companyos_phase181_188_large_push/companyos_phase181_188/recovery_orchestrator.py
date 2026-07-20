class RecoveryOrchestrator:
    """187: preserve operation through recoverable component failures."""
    def recover(self,components):
        actions=[]
        for c in components:
            if c.get("healthy",True): continue
            attempts=int(c.get("attempts",0))
            action="restart_and_verify" if attempts<2 else "activate_fallback" if c.get("fallback") else "isolate_and_continue"
            actions.append({"component":c.get("name"),"action":action,"autonomous":True,"destructive":False})
        return actions
