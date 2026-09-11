from companyos.selfimprove import PerformanceBaseline, SandboxValidator, SelfImprovementBoundary

def test_baseline():
    assert PerformanceBaseline().build({"success_rate":1})["success_rate"]==1

def test_sandbox():
    p={"reversible":True}
    assert SandboxValidator().validate(p,[{"passed":True}])["safe_for_canary"]

def test_boundary():
    assert SelfImprovementBoundary().evaluate({"kind":"financial_authority"})["requires_approval"]
