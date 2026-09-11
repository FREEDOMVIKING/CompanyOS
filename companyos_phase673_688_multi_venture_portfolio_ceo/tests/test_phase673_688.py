from companyos_phase673_688 import DuplicateAvoidance, PortfolioPriority, CompanyCreationOrchestrator

def test_duplicate_avoidance():
    existing=[{"venture_id":"v1","name":"Workflow Automation","problem":"manual workflow"}]
    candidate={"name":"Workflow Automation Tool","problem":"manual workflow"}
    assert DuplicateAvoidance().check(candidate,existing)["duplicate_risk"] is True

def test_portfolio_priority():
    score=PortfolioPriority().score({
        "validation_score":8,"revenue_signal":6,"roi_score":7,
        "resource_efficiency":1.2,"retention_rate":0.7
    })
    assert score>0

def test_company_creation_gate():
    result=CompanyCreationOrchestrator().prepare(
        {"name":"New Venture","category":"saas","problem":"different problem","thesis":"x"},
        []
    )
    assert result["success"] is True
    assert result["automatic_legal_entity_creation"] is False
