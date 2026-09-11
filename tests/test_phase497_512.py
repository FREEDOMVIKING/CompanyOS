from companyos_phase497_512 import MissionGenerator, DependencyResolver, EventRouter

def test_generates_research_for_opportunity_stage():
    missions = MissionGenerator().generate({"current_stage":"opportunity"}, {})
    assert missions[0]["mission_type"] == "research"

def test_resolves_validation_dependency():
    mission = {
        "mission_id":"m","mission_type":"validation",
        "blocked_on":["validation_evidence"],"context":{}
    }
    result = DependencyResolver().resolve(mission, {"validation_metrics":{"x":1}})
    assert result["mission"]["blocked_on"] == []

def test_event_router():
    assert EventRouter().route("operations_metrics_ready") == "resume_blocked"
