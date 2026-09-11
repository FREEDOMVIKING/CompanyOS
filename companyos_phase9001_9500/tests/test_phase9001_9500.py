from companyos.actiongov import ActionPolicyEngine, ActionRiskScorer, BudgetEnforcer

def test_policy():
    assert ActionPolicyEngine().evaluate({"kind":"production_deploy"})["requires_approval"]

def test_risk():
    assert ActionRiskScorer().score({"kind":"internal_analysis","external":False,"reversible":True})["risk_level"]=="low"

def test_budget():
    assert BudgetEnforcer().evaluate({"amount":100},1000)["allowed"]
