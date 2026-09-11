from companyos.productops import ProductQualityGate, AdoptionEngine, ProductAuthorityBoundary

def test_quality():
    assert ProductQualityGate().evaluate({
        "tests_passed":True,"security_passed":True,"performance_passed":True,
        "rollback_ready":True,"observability_ready":True})["passed"]

def test_adoption():
    assert AdoptionEngine().analyze([{"activation":.9,"engagement":.9,"retention":.9}])[0]["action"]=="scale_onboarding"

def test_boundary():
    assert ProductAuthorityBoundary().evaluate({"kind":"public_launch"})["requires_approval"]
