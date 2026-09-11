import uuid
from companyos.treasuryops import SpendController, TreasuryPolicy, TreasuryReconciler
from .approval_queue import PaymentApprovalQueue

class PaymentOrchestrator:
    def __init__(self, root, connector, allowlist=None, policy=None):
        self.root = root
        self.connector = connector
        self.allowlist = set(allowlist or [])
        self.policy = policy or TreasuryPolicy.from_env()
        self.controller = SpendController(root, policy=self.policy)
        self.approvals = PaymentApprovalQueue(root)

    def request_transfer(self, *, amount, destination, purpose="", daily_loss=0.0):
        bal = self.connector.get_balance()
        if not bal.get("success"):
            return {"success":False,"stage":"balance","details":bal}

        decision = self.controller.authorize(
            amount=amount,
            balance=bal.get("balance",0),
            destination=destination,
            allowlist=self.allowlist,
            daily_loss=daily_loss,
            purpose=purpose
        )

        if decision["decision"] == "blocked":
            return {
                "success":False,
                "status":"blocked",
                "decision":decision
            }

        if decision["decision"] == "approval_required":
            approval = self.approvals.enqueue({
                "request_id":"payreq_" + uuid.uuid4().hex[:16],
                "amount":float(amount),
                "destination":destination,
                "purpose":purpose,
                "decision":decision
            })
            return {
                "success":True,
                "status":"queued_for_approval",
                "approval":approval
            }

        idem = "companyos_" + uuid.uuid4().hex
        tx = self.connector.execute_transfer(
            amount=amount,
            destination=destination,
            memo=purpose,
            idempotency_key=idem
        )
        if not tx.get("success"):
            return {"success":False,"status":"connector_failed","transaction":tx}

        self.controller.record_execution(
            amount=amount,
            destination=destination,
            tx_id=tx.get("tx_id"),
            purpose=purpose
        )

        reconciliation = TreasuryReconciler().reconcile(
            self.controller.ledger.rows(),
            self.connector.list_transactions()
        )

        return {
            "success":True,
            "status":"executed",
            "transaction":tx,
            "reconciliation":reconciliation
        }
