from companyos.cicdops import CIQualityGate, SecurityGate, DeploymentGate

def test_quality_gate():
    assert CIQualityGate().evaluate({"lint":True,"static_analysis":True,"unit_tests":True,"integration_tests":True})["passed"]

def test_security_gate():
    assert SecurityGate().evaluate({"security_scan":True,"dependency_scan":True,"secrets_scan":True})["passed"]

def test_prod_gate_requires_approval():
    g=DeploymentGate().evaluate({"promotion_ready":True},{"passed":True},approval=False)
    assert g["production_deploy_allowed"] is False
