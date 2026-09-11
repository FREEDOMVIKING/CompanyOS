from companyos.integrationops import IntegrationOpsStatus

def test_status():
    s = IntegrationOpsStatus().status()
    assert s["stage_router_to_real_executor"] is True
    assert s["treasury_gate_preserved"] is True
    assert s["launch_gate_preserved"] is True
