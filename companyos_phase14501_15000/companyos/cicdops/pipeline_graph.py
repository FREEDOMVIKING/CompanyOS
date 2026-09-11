class PipelineGraph:
    STAGES = [
        "checkout",
        "lint",
        "static_analysis",
        "unit_tests",
        "integration_tests",
        "security_scan",
        "dependency_scan",
        "build_artifact",
        "staging_deploy",
        "smoke_tests",
        "health_check",
        "approval_gate",
        "production_deploy",
        "postdeploy_verify",
        "rollback_if_failed",
        "release_record"
    ]

    def build(self):
        return {
            "stages": self.STAGES,
            "edges": [[self.STAGES[i], self.STAGES[i+1]] for i in range(len(self.STAGES)-1)]
        }
