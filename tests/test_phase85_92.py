from companyos_phase85_92 import DecisionQuality,RiskRegister,CEOOrchestrator
def test_low_quality_block_recommendation():
    assert DecisionQuality().score({"evidence":0,"reversibility":0,"clarity":0,"downside_risk":1})["recommendation"]=="do_not_execute"
def test_risk_sort():
    assert RiskRegister().assess([{"name":"a","likelihood":1,"impact":1},{"name":"b","likelihood":5,"impact":5}])[0]["name"]=="b"
def test_ceo_cycle_no_external_action():
    assert CEOOrchestrator().run({})["external_action_taken"] is False
