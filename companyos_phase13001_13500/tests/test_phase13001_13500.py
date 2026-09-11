from companyos.customerops import CustomerHealthEngine, SLAEngine, CustomerAuthorityBoundary
def test_health():
    assert CustomerHealthEngine().score([{"usage":1,"satisfaction":1,"payment_health":1,"support_friction":0}])[0]["health"]=="healthy"
def test_sla():
    assert SLAEngine().evaluate([{"ticket_id":"t","sla_minutes":60,"elapsed_minutes":90}])["sla_ok"] is False
def test_boundary():
    assert CustomerAuthorityBoundary().evaluate({"kind":"change_contract"})["requires_approval"]
