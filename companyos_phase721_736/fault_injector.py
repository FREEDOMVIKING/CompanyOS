class FaultInjector:
    """730: safe synthetic faults for recovery testing."""

    def malformed_mission(self):
        return {
            "mission_id":"mission_fault_malformed",
            "mission_type":"unknown",
            "priority":0.1,
            "attempts":0,
            "blocked_on":[],
            "context":{"integration_test":True},
        }

    def blocked_mission(self):
        return {
            "mission_id":"mission_fault_blocked",
            "mission_type":"research",
            "priority":0.1,
            "attempts":0,
            "blocked_on":["synthetic_dependency"],
            "context":{"integration_test":True,"venture_id":"venture_fault_test"},
        }
