import os
from pathlib import Path
from .wallet_binding import ExistingWalletBinding

class SolanaExecutionReadiness:
    def __init__(self, root):
        self.root = Path(root)

    def inspect(self):
        wallet = ExistingWalletBinding(self.root).inspect()
        signer = os.getenv("MULTICHAIN_SIGNER_COMMAND", "").strip()
        rpc = os.getenv("SOLANA_RPC_URL", "").strip()
        live = os.getenv("COMPANYOS_ENABLE_LIVE_FINANCIAL_EXECUTION", "").strip().lower() in {"1","true","yes","on"}

        return {
            "wallet": wallet,
            "solana_rpc_configured": bool(rpc),
            "signer_command_configured": bool(signer),
            "signer_command_value_exposed": False,
            "multichain_adapter_present": wallet["multichain_adapter_present"],
            "treasury_gate_expected": True,
            "preflight_required": True,
            "receipt_verification_required": True,
            "live_financial_execution_enabled": live,
            "ready_for_dry_run": bool(rpc and signer and wallet["multichain_adapter_present"]),
            "ready_for_live": False,
            "note": "Live readiness remains false until dry-run/preflight and receipt-verification checks pass."
        }
