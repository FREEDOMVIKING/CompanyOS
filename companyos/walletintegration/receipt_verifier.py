from companyos.solanasim.rpc import SolanaRpcClient


class OnChainReceiptVerifier:
    def __init__(self, rpc=None):
        self.rpc = rpc or SolanaRpcClient()

    def verify(self, execution_result):
        r = execution_result or {}

        tx_id = (
            r.get("txid")
            or r.get("tx_id")
            or r.get("signature")
            or r.get("transaction_hash")
            or r.get("hash")
        )

        success = bool(r.get("success"))
        adapter_status = r.get("status")

        # Fail closed unless the adapter reports success and gives us
        # concrete transaction evidence.
        if not success or not tx_id:
            return {
                "passed": False,
                "tx_id": tx_id,
                "success_flag": success,
                "adapter_status": adapter_status,
                "confirmation_status": None,
                "confirmation_error": None,
                "evidence_present": bool(tx_id),
                "rpc_checked": False,
            }

        rpc_result = self.rpc.signature_status(tx_id)

        if not rpc_result.get("success"):
            return {
                "passed": False,
                "tx_id": tx_id,
                "success_flag": success,
                "adapter_status": adapter_status,
                "confirmation_status": None,
                "confirmation_error": rpc_result,
                "evidence_present": True,
                "rpc_checked": True,
            }

        values = rpc_result.get("result", {}).get("value") or []
        sig_status = values[0] if values else None

        if not sig_status:
            return {
                "passed": False,
                "tx_id": tx_id,
                "success_flag": success,
                "adapter_status": adapter_status,
                "confirmation_status": None,
                "confirmation_error": "signature_not_found",
                "evidence_present": True,
                "rpc_checked": True,
            }

        confirmation_status = sig_status.get("confirmationStatus")
        err = sig_status.get("err")

        if err is not None:
            state = "failed"
            passed = False
        elif confirmation_status in {"confirmed", "finalized"}:
            state = confirmation_status
            passed = True
        else:
            state = "pending"
            passed = False

        return {
            "passed": passed,
            "state": state,
            "tx_id": tx_id,
            "success_flag": success,
            "adapter_status": adapter_status,
            "confirmation_status": confirmation_status,
            "confirmation_error": err,
            "evidence_present": True,
            "rpc_checked": True,
        }
