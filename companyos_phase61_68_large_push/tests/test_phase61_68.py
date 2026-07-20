from companyos_phase61_68 import TaskGraph, GovernanceEngine

def test_dependency_deadlock():
    result = TaskGraph().order([
        {"id":"a","depends_on":["b"]},
        {"id":"b","depends_on":["a"]},
    ])
    assert result["success"] is False

def test_governance_high_risk_needs_approval():
    result = GovernanceEngine().classify({
        "external":True,"financial":True,"irreversible":True
    })
    assert result["approval_required"] is True
    assert result["allowed"] is False
