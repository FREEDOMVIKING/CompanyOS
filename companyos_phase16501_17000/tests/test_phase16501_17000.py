from companyos.ceointelligence import AutonomousPlanner, ApprovalClassifier, CEOIntelligenceStatus

def test_plan_validation():
    p = {
        "tasks":[{
            "department":"research",
            "instruction":"do research"
        }]
    }
    assert AutonomousPlanner().validate(p)["passed"] is True

def test_approval_gate():
    assert ApprovalClassifier().classify({"kind":"production_deploy"})["requires_approval"] is True
    assert ApprovalClassifier().classify({"kind":"research"})["requires_approval"] is False

def test_status():
    assert CEOIntelligenceStatus().status()["success"] is True
