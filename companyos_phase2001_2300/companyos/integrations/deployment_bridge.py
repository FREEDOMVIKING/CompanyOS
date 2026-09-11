class DeploymentBridge:
    def plan(self, environment, artifact, rollback_ref=None):
        return {
            "environment":environment,
            "artifact":artifact,
            "rollback_ref":rollback_ref,
            "steps":["preflight","deploy","smoke_test","health_check"],
            "requires_approval":environment=="production"
        }
