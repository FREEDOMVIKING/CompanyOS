import json
from pathlib import Path

class ExistingWalletBinding:
    def __init__(self, root):
        self.root = Path(root)
        self.binding_path = self.root / ".companyos_runtime" / "crypto_wallet_binding.json"
        self.adapter_path = self.root / "agents" / "multichain_execution_adapter.py"

    def inspect(self):
        binding = None
        if self.binding_path.exists():
            try:
                binding = json.loads(self.binding_path.read_text(encoding="utf-8"))
            except Exception:
                binding = None

        return {
            "binding_file_present": self.binding_path.exists(),
            "binding": binding,
            "multichain_adapter_present": self.adapter_path.exists(),
            "multichain_adapter_path": str(self.adapter_path),
        }
