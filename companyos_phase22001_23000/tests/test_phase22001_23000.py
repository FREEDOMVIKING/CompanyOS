from companyos.paymentops import SandboxPaymentConnector, PaymentOpsStatus

def test_sandbox_transfer():
    c = SandboxPaymentConnector(100)
    r = c.execute_transfer(amount=10, destination="x")
    assert r["success"] is True
    assert c.get_balance()["balance"] == 90

def test_status_safe():
    s = PaymentOpsStatus().status()
    assert s["real_provider_connected"] is False
    assert s["real_money_enabled"] is False
