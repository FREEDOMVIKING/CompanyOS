import os
from pathlib import Path

class MultichainReadiness:
    def __init__(self, root):
        self.root = Path(root)

    def inspect(self):
        adapter = self.root / "agents" / "multichain_execution_adapter.py"
        signer = os.getenv("MULTICHAIN_SIGNER_COMMAND", "").strip()
        return {
            "adapter_present": adapter.exists(),
            "adapter_path": str(adapter),
            "signer_command_configured": bool(signer),
            "solana_rpc_configured": bool(os.getenv("SOLANA_RPC_URL","").strip()),
            "evm_rpc_configured": bool(os.getenv("EVM_RPC_URL","").strip()),
            "bitcoin_rpc_configured": bool(os.getenv("BITCOIN_RPC_URL","").strip()),
            "evm_key_reference_present": bool(os.getenv("EVM_PRIVATE_KEY_HEX","").strip()),
            "btc_key_reference_present": bool(os.getenv("BITCOIN_PRIVATE_KEY_WIF","").strip()),
            "live_financial_execution_enabled": os.getenv("COMPANYOS_ENABLE_LIVE_FINANCIAL_EXECUTION","").strip().lower() in {"1","true","yes","on"},
        }
