class LaunchPlan:
    """618: controlled launch stages."""

    def build(self):
        return {
            "stages":["internal","limited_beta","measured_release"],
            "required_before_each_stage":["health_check","telemetry","rollback_plan"],
            "automatic_irreversible_launch":False,
            "promotion_rule":"advance only on measured evidence",
        }
