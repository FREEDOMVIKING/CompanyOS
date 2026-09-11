import importlib.util
import os
from pathlib import Path

from companyos.moneyops import FinancialKillSwitch, IdempotencyStore, ReceiptStore
from companyos.treasuryops import SpendController, TreasuryPolicy
from .receipt_verifier import OnChainReceiptVerifier

class SolanaExecutionGate:
    def __init__(self, root, allowlist=None, policy=None):
        self.root = Path(root)
        self.allowlist = set(allowlist or [])
        self.policy = policy or TreasuryPolicy.from_env()
        self.controller = SpendController(self.root, policy=self.policy)
        self.kill = FinancialKillSwitch(self.root)
        self.idempotency = IdempotencyStore(self.root)
        self.receipts = ReceiptStore(self.root)
        self.verifier = OnChainReceiptVerifier()
        self.adapter = self._load_adapter()

    def _load_adapter(self):
        path = self.root / "agents" / "multichain_execution_adapter.py"
        if not path.exists():
            raise FileNotFoundError(f"missing_multichain_execution_adapter:{path}")
        spec = importlib.util.spec_from_file_location("companyos_live_multichain_adapter", str(path))
        if not spec or not spec.loader:
            raise RuntimeError("multichain_adapter_load_failed")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _execute(self, payload):
        fn = getattr(self.adapter, "execute", None)
        if not callable(fn):
            raise RuntimeError("existing_adapter_execute_not_found")
        out = fn(payload)
        return out if isinstance(out, dict) else {"success": True, "output": out}

    def prepare_and_execute(
        self,
        *,
        amount,
        balance,
        destination,
        source=None,
        token_mint=None,
        memo="",
        idempotency_key,
        daily_loss=0.0,
        dry_run=True,
        signing_authorized=False,
    ):
        if self.kill.engaged():
            return {"success":False,"status":"financial_kill_switch_engaged"}

        prior = self.idempotency.get(idempotency_key)
        if prior is not None:
            return {
                "success": True,
                "status": "idempotent_replay",
                "idempotency_key": idempotency_key,
                "result": prior,
            }

        decision = self.controller.authorize(
            amount=amount,
            balance=balance,
            destination=destination,
            allowlist=self.allowlist,
            daily_loss=daily_loss,
            purpose=memo or "Solana transfer",
        )

        if decision["decision"] == "blocked":
            out = {"success":False,"status":"treasury_blocked","decision":decision}
            self.idempotency.put(idempotency_key, out)
            return out

        if decision["decision"] == "approval_required":
            out = {"success":True,"status":"approval_required","decision":decision}
            self.idempotency.put(idempotency_key, out)
            return out

        live_enabled = os.getenv(
            "COMPANYOS_ENABLE_LIVE_FINANCIAL_EXECUTION",""
        ).strip().lower() in {"1","true","yes","on"}

        payload = {
            "chain":"solana",
            "source":source,
            "destination":destination,
            "amount_native":float(amount),
            "amount":float(amount),
            "memo":memo,
            "signing_authorized":bool(signing_authorized and live_enabled and not dry_run),
        }
        if token_mint:
            payload["token_mint"] = token_mint

        # Dry-run/preflight mode intentionally prevents signer authorization.
        if dry_run or not live_enabled:
            payload["signing_authorized"] = False

        result = self._execute(payload)

        # Expected adapter outcomes during safe validation include:
        # not_authorized, preflight_failed, adapter_requires_provider_specific_implementation,
        # use_existing_solana_sol_executor, or a successful non-broadcast preparation response.
        if dry_run or not live_enabled:
            out = {
                "success": True,
                "status": "dry_run_complete",
                "adapter_result": result,
                "idempotency_key": idempotency_key,
                "broadcast_attempted": False,
            }
            self.idempotency.put(idempotency_key, out)
            return out

        if not signing_authorized:
            out = {
                "success": True,
                "status":"signing_authorization_required",
                "idempotency_key":idempotency_key
            }
            self.idempotency.put(idempotency_key, out)
            return out

        verification = self.verifier.verify(result)
        receipt = self.receipts.append({
            "chain":"solana",
            "amount":float(amount),
            "destination":destination,
            "idempotency_key":idempotency_key,
            "adapter_result":result,
            "verification":verification,
        })

        if verification["passed"]:
            self.controller.record_execution(
                amount=amount,
                destination=destination,
                tx_id=verification["tx_id"],
                purpose=memo or "Solana transfer",
            )

        out = {
            "success": bool(verification["passed"]),
            "status": "verified_onchain_execution" if verification["passed"] else "execution_unverified",
            "verification": verification,
            "receipt": receipt,
        }
        self.idempotency.put(idempotency_key, out)
        return out
