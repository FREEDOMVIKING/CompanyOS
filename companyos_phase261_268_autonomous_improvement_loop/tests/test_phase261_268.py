from companyos_phase261_268 import ImprovementPlanner, CapabilityMapper, VerificationPolicy

def test_planner_internal_only():
    p = ImprovementPlanner().propose({"signals":{}})
    assert p["internal_only"] is True

def test_mapper():
    m = CapabilityMapper().map({"improvement":"runtime_health_diagnostics"})
    assert m["module_name"] == "generated_runtime_health_diagnostics"

def test_verification_policy():
    result = VerificationPolicy().evaluate({
        "success":True,
        "regression":{"success":True},
        "registered":{"verified":True},
    })
    assert result["approved"] is True
