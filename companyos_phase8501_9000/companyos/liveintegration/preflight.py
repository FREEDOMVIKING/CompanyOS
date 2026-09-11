class LivePreflight:
    def evaluate(self, readiness):
        required=["connector_certified","credentials_ready","health_ok","rollback_ready","audit_ready"]
        missing=[k for k in required if not readiness.get(k,False)]
        return {"passed":not missing,"missing":missing}
