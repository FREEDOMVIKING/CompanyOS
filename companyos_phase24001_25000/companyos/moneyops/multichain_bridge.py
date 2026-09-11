import importlib.util
import json
import os
import uuid
from pathlib import Path

from companyos.treasuryops import SpendController, TreasuryPolicy
from .kill_switch import FinancialKillSwitch
from .idempotency import IdempotencyStore
from .receipt_store import ReceiptStore

class TreasuryGatedMultichainBridge:
    """
    Mandatory treasury gate in front of the existing
    agents/multichain_execution_adapter.py execute(payload) path.
    """

    def __init__(self, root, allowlist=None, policy=None):
        self.root = Path(root)
        self.allowlist = set(allowlist or [])
        self.policy = policy or TreasuryPolicy.from_env()
        self.controller = SpendController(self.root, policy=self.policy)
        self.kill_switch = FinancialKillSwitch(self.root)
        self.idempotency = IdempotencyStore(self.root)
        self.receipts = ReceiptStore(self.root)
        self.adapter = self._load_adapter()

    def _load_adapter(self):
        path = self.root / "agents" / "multichain_execution_adapter.py"
        if not path.exists():
            raise FileNotFoundError(f"missing_multichain_adapter:{path}")

        spec = importlib.util.spec_from_file_location("companyos_live_multichain_adapter", str(path))
        if not spec or not spec.loader:
            raise RuntimeError("multichain_adapter_load_failed")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _execute_existing(self, payload):
        fn = getattr(self.adapter, "execute", None)
        if not callable(fn):
            raise RuntimeError("existing_adapter_execute_not_found")
        result = fn(payload)
        return result if isinstance(result, dict) else {"success": True, "result": result}

    def authorize_and_execute(
        self,
        *,
        chain,
        amount,
        balance,
        destination,
        source=None,
        token_mint=None,
        token_contract=None,
        memo="",
        daily_loss=0.0,
        idempotency_key=None,
        signing_authorized=False,
        dry_run=True,
    ):
        if self.kill_switch.engaged():
            return {
                "success": False,
                "status": "financial_kill_switch_engaged",
            }

        key = idempotency_key or f"companyos_{uuid.uuid4().hex}"
        prior = self.idempotency.get(key)
        if prior is not None:
            return {
                "success": True,
                "status": "idempotent_replay",
                "idempotency_key": key,
                "result": prior,
            }

        decision = self.controller.authorize(
            amount=amount,
            balance=balance,
            destination=destination,
            allowlist=self.allowlist,
            daily_loss=daily_loss,
            purpose=memo or f"{chain} transfer",
        )

        if decision["decision"] == "blocked":
            out = {
                "success": False,
                "status": "treasury_blocked",
                "decision": decision,
                "idempotency_key": key,
            }
            self.idempotency.put(key, out)
            return out

        if decision["decision"] == "approval_required":
            out = {
                "success": True,
                "status": "approval_required",
                "decision": decision,
                "idempotency_key": key,
            }
            self.idempotency.put(key, out)
            return out

        live_enabled = os.getenv("COMPANYOS_ENABLE_LIVE_FINANCIAL_EXECUTION","").strip().lower() in {"1","true","yes","on"}
        if dry_run or not live_enabled:
            out = {
                "success": True,
                "status": "dry_run_authorized",
                "chain": chain,
                "amount": float(amount),
                "destination": destination,
                "decision": decision,
                "idempotency_key": key,
                "live_enabled": live_enabled,
            }
            self.idempotency.put(key, out)
            return out

        if not signing_authorized:
            out = {
                "success": True,
                "status": "signing_authorization_required",
                "idempotency_key": key,
            }
            self.idempotency.put(key, out)
            return out

        payload = {
            "chain": str(chain).lower(),
            "source": source,
            "destination": destination,
            "amount_native": float(amount),
            "amount": float(amount),
            "memo": memo,
            "signing_authorized": True,
        }
        if token_mint:
            payload["token_mint"] = token_mint
        if token_contract:
            payload["token_contract"] = token_contract

        result = self._execute_existing(payload)

        receipt = {
            "idempotency_key": key,
            "chain": chain,
            "amount": float(amount),
            "destination": destination,
            "result": result,
        }
        self.receipts.append(receipt)

        if result.get("success"):
            tx_id = (
                result.get("tx_id")
                or result.get("signature")
                or result.get("transaction_hash")
                or result.get("hash")
            )
            if tx_id:
                self.controller.record_execution(
                    amount=amount,
                    destination=destination,
                    tx_id=tx_id,
                    purpose=memo or f"{chain} transfer",
                )

        out = {
            "success": bool(result.get("success")),
            "status": "executed" if result.get("success") else "execution_failed",
            "idempotency_key": key,
            "adapter_result": result,
        }
        self.idempotency.put(key, out)
        return out
