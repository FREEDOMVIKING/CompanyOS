from companyos_phase293_300 import CycleFlatteningPolicy, OpportunityScoring, OpportunityPipeline

def test_flattening():
    assert CycleFlatteningPolicy().supervisor_limits_for_rounds(3)["total_expected_cycles"] == 3

def test_scoring_max():
    score = OpportunityScoring().score({
        "demand":10,"speed_to_revenue":10,"margin":10,"automation":10,
        "competition_advantage":10,"recurring_revenue":10,"capital_efficiency":10
    })
    assert score == 10.0

def test_validation_plan_present():
    ranked = OpportunityPipeline().rank([{
        "name":"x","problem":"p","customer":"c","solution":"s",
        "revenue_model":"r","evidence":["e"],"metrics":{"demand":5}
    }])
    assert "validation_plan" in ranked[0]
