from companyos.enterpriseopt import EnterpriseScorecard, DepartmentCapacityPlanner, EnterpriseAuthorityBoundary

def test_score():
    assert EnterpriseScorecard().evaluate([{"growth":1,"margin":1,"retention":1,"reliability":1,"strategic_fit":1}])[0]["enterprise_score"]==1

def test_capacity():
    assert DepartmentCapacityPlanner().plan([{"name":"x","demand":2,"capacity":1}])[0]["action"]=="add_capacity"

def test_boundary():
    assert EnterpriseAuthorityBoundary().evaluate({"kind":"venture_retirement"})["requires_approval"]
