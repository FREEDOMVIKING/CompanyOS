from companyos.walletintegration import OnChainReceiptVerifier, WalletIntegrationStatus

def test_receipt_verification():
    # V65.64 confirmed-RPC receipt verification contract
    class ConfirmedRpc:
        def signature_status(self, tx_id):
            assert tx_id == "abc"
            return {
                "success": True,
                "result": {
                    "value": [
                        {
                            "confirmationStatus": "confirmed",
                            "err": None,
                        }
                    ]
                },
            }

    v = OnChainReceiptVerifier(rpc=ConfirmedRpc()).verify(
        {"success": True, "signature": "abc"}
    )
    assert v["passed"] is True
    assert v["rpc_checked"] is True
    assert v["confirmation_status"] == "confirmed"

def test_no_false_success():
    v = OnChainReceiptVerifier().verify({"success":True})
    assert v["passed"] is False

def test_safe_default():
    assert WalletIntegrationStatus().status()["live_execution_auto_enabled"] is False
