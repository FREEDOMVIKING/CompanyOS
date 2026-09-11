from .policy import TreasuryPolicy
from .ledger import TreasuryLedger
from .risk_engine import TreasuryRiskEngine

class SpendController:
    def __init__(self, root, policy=None):
        self.root = root
        self.policy = policy or TreasuryPolicy.from_env()
        self.ledger = TreasuryLedger(root)

    def authorize(self, *, amount, balance, destination, allowlist=None, daily_loss=0.0, purpose=""):
        allowlist = set(allowlist or [])
        destination_allowed = destination in allowlist if self.policy.require_allowlist else True
        daily_spend = self.ledger.today_total("debit")

        risk = TreasuryRiskEngine().evaluate(
            amount=amount,
            balance=balance,
            destination_allowed=destination_allowed,
            daily_spend=daily_spend,
            daily_loss=daily_loss,
            policy=self.policy
        )

        decision = {
            "amount": float(amount),
            "destination": destination,
            "purpose": purpose,
            "risk": risk,
            "decision": (
                "autonomous_allowed" if risk["allowed"]
                else "approval_required" if risk["approval_required"]
                else "blocked"
            )
        }
        self.ledger.append({
            "direction":"decision",
            "amount":float(amount),
            "destination":destination,
            "purpose":purpose,
            "decision":decision["decision"]
        })
        return decision

    def record_execution(self, *, amount, destination, tx_id, purpose=""):
        return self.ledger.append({
            "direction":"debit",
            "amount":float(amount),
            "destination":destination,
            "tx_id":tx_id,
            "purpose":purpose,
            "status":"executed"
        })
