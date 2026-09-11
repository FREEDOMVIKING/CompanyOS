from companyos_phase529_544 import CandidateRouter, CandidateDeduper, QualityMissionGenerator

def test_router():
    c = {"decision":{"decision":"priority_validate"}}
    assert CandidateRouter().route(c) == "validation"

def test_deduper():
    a = {"theme":"x","quality_score":5}
    b = {"theme":"x","quality_score":7}
    out = CandidateDeduper().unique([a,b])
    assert len(out) == 1 and out[0]["quality_score"] == 7

def test_mission_generation():
    c = {
        "name":"X","theme":"workflow_automation","quality_score":7,
        "source_count":2,"evidence_links":[],"dimensions":{},
        "decision":{"decision":"validate"}
    }
    missions = QualityMissionGenerator().generate([c])
    assert missions[0]["mission_type"] == "validation"
