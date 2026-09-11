from companyos.connectors import ConnectorRegistry, CapabilityDiscovery, ConnectorApprovalRouter

def test_registry(tmp_path):
    r=ConnectorRegistry(tmp_path)
    r.register("x","provider",["research"],.9)
    assert r.list_enabled()[0]["name"]=="x"

def test_capabilities(tmp_path):
    r=ConnectorRegistry(tmp_path)
    r.register("x","provider",["research"],.9)
    assert "research" in CapabilityDiscovery().discover(r.list_enabled())

def test_gate():
    assert ConnectorApprovalRouter().route([{"kind":"production_deploy"}])["approval_queue"]
