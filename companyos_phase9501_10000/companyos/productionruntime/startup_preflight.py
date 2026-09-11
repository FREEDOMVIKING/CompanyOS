class StartupPreflight:
    def evaluate(self, checks):
        required=["state_store","checkpoint","queue","memory","approval_queue","health","config"]
        missing=[k for k in required if not checks.get(k,False)]
        return {"passed":not missing,"missing":missing}
