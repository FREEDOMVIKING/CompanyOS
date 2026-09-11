class DeploymentAdapter:
    def plan(self, environment, artifact, rollback_ref=None):
        return {
            "capability":"deploy",
            "environment":environment,
            "artifact":artifact,
            "rollback_ref":rollback_ref,
            "steps":["preflight","deploy","smoke_test","health_check","rollback_if_failed"],
            "status":"planned"
        }
