from companyos_phase577_592 import StageAdvancer, ProgressGuard, MissionFactory

def test_stage_advancer():
    assert StageAdvancer().next_stage("validation",{"validation_decision":"go_to_mvp"}) == "build"

def test_progress_guard():
    result = ProgressGuard().evaluate({"stagnant_cycles":2,"last_outcome_score":0})
    assert result["action"] == "pause_and_research"

def test_mission_factory():
    mission = MissionFactory().build("v1","continue_bounded_build",{})
    assert mission["mission_type"] == "build"
