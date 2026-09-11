from companyos.livegate import OneShotAuthorization, LiveReadinessGate
from companyos.transactionops import TransactionLifecycle
from companyos.controlledexec.execution_receipt import ControlledExecutionReceipt
from companyos.controlledexec.postlock import PostExecutionLock

class ControlledExecutionOrchestrator:
    def __init__(self, root, max_single_amount=0.01, min_reserve=0.01):
        self.root = root
        self.auth = OneShotAuthorization(root)
        self.readiness = LiveReadinessGate(root)
        self.tx = TransactionLifecycle(
            root,
            max_single_amount=max_single_amount,
            min_reserve=min_reserve
        )
        self.receipts = ControlledExecutionReceipt(root)
        self.postlock = PostExecutionLock(root)

    def prepare(
        self,
        *,
        token,
        destination,
        amount,
        balance,
        estimated_fee,
        allowlist=None,
        memo=""
    ):
        lock = self.postlock.status()
        if lock.get("locked"):
            return {"success":False,"status":"post_execution_lock_active","lock":lock}

        readiness = self.readiness.evaluate()
        if not readiness.get("ready_for_controlled_live_review"):
            return {
                "success":False,
                "status":"controlled_live_readiness_not_met",
                "readiness":readiness
            }

        auth = self.auth.validate(token, amount, destination)
        if not auth.get("allowed"):
            return {"success":False,"status":auth.get("status"),"authorization":auth}

        prepared = self.tx.prepare(
            destination=destination,
            amount=amount,
            balance=balance,
            estimated_fee=estimated_fee,
            allowlist=allowlist,
            memo=memo
        )
        if not prepared.get("success"):
            return {
                "success":False,
                "status":"transaction_preparation_failed",
                "transaction":prepared
            }

        return {
            "success":True,
            "status":"controlled_execution_prepared",
            "authorization":auth,
            "transaction":prepared,
            "broadcast_allowed":False,
            "signing_allowed":False,
            "next_stage":"sign_and_broadcast_adapter_integration"
        }

    def finalize_no_broadcast(self, prepared_result, reason="validation_complete_no_broadcast"):
        receipt = self.receipts.append({
            "mode":"nonbroadcast",
            "success":bool((prepared_result or {}).get("success")),
            "status":(prepared_result or {}).get("status"),
            "reason":reason
        })
        lock = self.postlock.engage(reason)
        return {
            "success":True,
            "status":"controlled_execution_validation_finalized",
            "receipt":receipt,
            "post_execution_lock":lock,
            "broadcast_attempted":False
        }
