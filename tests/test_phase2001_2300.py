from companyos.integrations import IntegrationRegistry, DepartmentRouter, ExternalActionApprovalGate

def test_registry(tmp_path):
    r=IntegrationRegistry(tmp_path)
    r.register("x","provider",["research"])
    assert len(r.available("research"))==1

def test_routing():
    assert DepartmentRouter().route([{"task_type":"deploy"}])[0]["department"]=="operations"

def test_approval_gate():
    assert ExternalActionApprovalGate().evaluate({"kind":"production_deploy"})["requires_approval"] is True
