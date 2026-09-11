from companyos.walletsource import VerifiedWalletIdentity, ProposalSourceInjector, ExecutionSourceGuard
from companyos.moneyops import FinancialKillSwitch
from .transaction_policy import TransactionPolicy
from .duplicate_guard import DuplicatePaymentGuard
from .balance_guard import BalanceAndFeeGuard

class TransactionLifecycle:
    def __init__(self, root, max_single_amount=0.01, min_reserve=0.01):
        self.root = root
        self.identity_loader = VerifiedWalletIdentity(root)
        self.injector = ProposalSourceInjector()
        self.source_guard = ExecutionSourceGuard()
        self.kill = FinancialKillSwitch(root)
        self.policy = TransactionPolicy(max_single_amount, min_reserve)
        self.duplicates = DuplicatePaymentGuard(root)
        self.balance_guard = BalanceAndFeeGuard()
        self.min_reserve = float(min_reserve)

    def prepare(
        self,
        *,
        destination,
        amount,
        balance,
        estimated_fee,
        allowlist=None,
        token=None,
        memo=""
    ):
        if self.kill.engaged():
            return {"success":False,"status":"financial_kill_switch_engaged"}

        identity = self.identity_loader.load()
        if not identity.get("success"):
            return {"success":False,"status":"verified_wallet_identity_missing"}

        injected = self.injector.inject({
            "chain":"solana",
            "destination":destination,
            "amount":float(amount),
            "token":token,
            "memo":memo
        }, identity)

        if not injected.get("success"):
            return injected

        proposal = injected["proposal"]

        source_check = self.source_guard.validate(proposal, identity)
        if not source_check.get("allowed"):
            return {"success":False,"status":source_check.get("status"),"source_check":source_check}

        policy = self.policy.validate(amount, destination, allowlist=allowlist)
        if not policy.get("allowed"):
            return {"success":False,"status":policy.get("status"),"policy":policy}

        balance_check = self.balance_guard.validate(
            balance, amount, estimated_fee, self.min_reserve
        )
        if not balance_check.get("allowed"):
            return {"success":False,"status":balance_check.get("status"),"balance_check":balance_check}

        fp = self.duplicates.fingerprint(
            proposal["source"], destination, amount, token, memo
        )
        if self.duplicates.seen(fp):
            return {"success":False,"status":"duplicate_payment_blocked","fingerprint":fp}

        return {
            "success":True,
            "status":"transaction_ready_for_nonbroadcast_validation",
            "proposal":proposal,
            "policy":policy,
            "balance_check":balance_check,
            "fingerprint":fp,
            "broadcast_allowed":False,
            "signing_allowed":False,
            "next_stage":"simulate_and_validate"
        }
