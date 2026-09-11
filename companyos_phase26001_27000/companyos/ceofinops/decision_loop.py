from .financial_planner import FinancialPlanner
from .expected_value import ExpectedValueEngine
from .capital_allocator import CapitalAllocator
from companyos.moneyops import TreasuryGatedMultichainBridge

class CEOFinancialDecisionLoop:
    def __init__(self, root, allowlist=None, policy=None):
        self.root = root
        self.allowlist = set(allowlist or [])
        self.policy = policy
        self.planner = FinancialPlanner()
        self.ev = ExpectedValueEngine()

    def evaluate_opportunities(self, opportunities, available_capital, reserve_floor):
        evaluated = []
        for opp in opportunities or []:
            plan = self.planner.build_plan(opp)
            evaluated.append({
                "plan": plan,
                "evaluation": self.ev.evaluate(plan),
            })
        return CapitalAllocator().allocate(
            evaluated,
            available_capital=available_capital,
            reserve_floor=reserve_floor,
        )

    def authorize_plan(self, plan, balance, daily_loss=0.0, dry_run=True):
        bridge = TreasuryGatedMultichainBridge(
            self.root,
            allowlist=self.allowlist,
            policy=self.policy,
        )
        return bridge.authorize_and_execute(
            chain=plan.get("chain", "solana"),
            amount=plan.get("required_capital", 0),
            balance=balance,
            destination=plan.get("destination") or "",
            source=plan.get("source"),
            token_mint=plan.get("token_mint"),
            token_contract=plan.get("token_contract"),
            memo=plan.get("purpose",""),
            daily_loss=daily_loss,
            signing_authorized=False,
            dry_run=dry_run,
        )
