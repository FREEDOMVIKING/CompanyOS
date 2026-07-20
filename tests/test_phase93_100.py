from companyos_phase93_100 import MissionBoard, AutonomousQueue, ExternalActionRouter, ProductionReadiness

def test_invalid_mission_transition():
    result = MissionBoard().transition({"status":"completed"}, "active")
    assert result["transition_ok"] is False

def test_queue_skips_external_work():
    rows = AutonomousQueue().select([{"id":"x","requires_external_action":True}])
    assert rows == []

def test_high_impact_action_needs_approval():
    route = ExternalActionRouter().route({"type":"purchase"})
    assert route["dispatch_allowed"] is False

def test_readiness_gate():
    result = ProductionReadiness().evaluate({})
    assert result["ready"] is False
