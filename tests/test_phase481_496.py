from companyos_phase481_496 import EvidenceGate, MissionScheduler, SchedulerRuntime

def test_validation_gate():
    gate = EvidenceGate().evaluate("validation", {
        "landing_page_visits":100,
        "qualified_leads":5,
    })
    assert gate["ready"] is True

def test_mission_scheduler():
    missions = [
        {"mission_id":"a","priority":0.8,"attempts":0,"blocked_on":[]},
        {"mission_id":"b","priority":0.9,"attempts":0,"blocked_on":["x"]},
    ]
    result = MissionScheduler().order(missions)
    assert result["ready"][0]["mission_id"] == "a"
    assert result["blocked"][0]["mission_id"] == "b"

def test_runtime():
    assert SchedulerRuntime().status()["status"] == "phase496_evidence_gate_scheduler_ready"
