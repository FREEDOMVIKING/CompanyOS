import json
from pathlib import Path
from datetime import datetime, timezone

class WalletBindingWriter:
    def __init__(self, root):
        self.root = Path(root)
        self.path = self.root / ".companyos_runtime" / "crypto_wallet_binding.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, wallet_candidate, metadata=None):
        if not wallet_candidate:
            return {"success":False,"status":"wallet_candidate_missing"}

        data = {
            "wallet_file": wallet_candidate["path"],
            "wallet_relative_path": wallet_candidate.get("relative_path"),
            "wallet_name": wallet_candidate.get("name"),
            "discovery_score": wallet_candidate.get("score"),
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "contains_private_key_material": False,
        }
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return {
            "success":True,
            "status":"wallet_binding_created",
            "binding_path":str(self.path),
            "binding":data,
        }
