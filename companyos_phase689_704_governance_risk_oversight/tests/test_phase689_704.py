from companyos_phase689_704 import ApprovalGateway, PreflightCheck, RollbackPolicy

def test_research_autonomous():
    assert ApprovalGateway().evaluate({"action_type":"research"})["approval_required"] is False

def test_sensitive_action_gated():
    assert ApprovalGateway().evaluate({"action_type":"sign_contract"})["approval_required"] is True

def test_rollback_required():
    r=RollbackPolicy().evaluate({"mutates_state":True,"reversible":False})
    assert r["autonomous_execution_allowed"] is False
