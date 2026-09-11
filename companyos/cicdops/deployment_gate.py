class DeploymentGate:
    def evaluate(self, manifest, staging, approval=False):
        preconditions = bool(manifest.get("promotion_ready")) and bool(staging.get("passed"))
        return {
            "preconditions_passed": preconditions,
            "requires_approval": True,
            "approved": bool(approval),
            "production_deploy_allowed": preconditions and bool(approval)
        }
