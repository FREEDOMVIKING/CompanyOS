from companyos.moneyops import TreasuryGatedMultichainBridge

class FinancialSimulationEngine:
    def __init__(self, root, allowlist=None, policy=None):
        self.bridge = TreasuryGatedMultichainBridge(
            root,
            allowlist=allowlist or set(),
            policy=policy
        )

    def simulate(self, intent, *, balance, daily_loss=0.0):
        return self.bridge.authorize_and_execute(
            chain=intent["chain"],
            amount=intent["amount"],
            balance=balance,
            destination=intent["destination"],
            source=intent.get("source"),
            token_mint=intent.get("token_mint"),
            token_contract=intent.get("token_contract"),
            memo=intent.get("purpose",""),
            daily_loss=daily_loss,
            idempotency_key=intent.get("idempotency_key"),
            signing_authorized=False,
            dry_run=True,
        )
