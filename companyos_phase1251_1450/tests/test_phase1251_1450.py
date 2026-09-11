from companyos.departments import ExecutiveOrchestrator

def test_executive_delegation(tmp_path):
    r=ExecutiveOrchestrator(tmp_path).delegate("test venture")
    assert r["success"] is True
    assert len(r["departments"]) == 7
    assert r["executive_confidence"] > .7

def test_irreversible_actions_are_gated(tmp_path):
    r=ExecutiveOrchestrator(tmp_path).delegate("test venture")
    kinds={x["action"]["kind"] for x in r["approval_queue"]}
    assert "contract_signature" in kinds
    assert "bank_transfer" in kinds
    assert "production_delete" in kinds

def test_memory_persists(tmp_path):
    ceo=ExecutiveOrchestrator(tmp_path)
    ceo.delegate("remember this")
    assert len(ceo.memory.recent()) > 0
