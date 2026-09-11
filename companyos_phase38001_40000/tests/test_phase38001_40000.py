from companyos.walletintegration import OnChainReceiptVerifier, WalletIntegrationStatus

def test_receipt_verification():
    v = OnChainReceiptVerifier().verify({"success":True,"signature":"abc"})
    assert v["passed"] is True

def test_no_false_success():
    v = OnChainReceiptVerifier().verify({"success":True})
    assert v["passed"] is False

def test_safe_default():
    assert WalletIntegrationStatus().status()["live_execution_auto_enabled"] is False
