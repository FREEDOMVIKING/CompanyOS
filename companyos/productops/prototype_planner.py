class PrototypePlanner:
    def plan(self, concept):
        return {
            "concept":concept,
            "steps":[
                "define_hypothesis",
                "identify_smallest_testable_behavior",
                "build_low_cost_prototype",
                "instrument_measurement",
                "test_with_target_users",
                "capture_evidence"
            ],
            "status":"prototype_plan_ready"
        }
