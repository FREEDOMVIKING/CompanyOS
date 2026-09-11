import json
from pathlib import Path

class SolanaIdentityProvider:
    def __init__(self, root):
        self.root = Path(root)
        self.paths = [
            Path.home() / "companyos_runtime" / "wallet_identity.json",
            self.root / ".companyos_runtime" / "wallet_identity.json",
        ]

    def get(self):
        for p in self.paths:
            if not p.exists():
                continue
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if data.get("chain") == "solana" and data.get("public_address"):
                return {"success":True,"public_address":data["public_address"],"path":str(p)}
        return {"success":False,"status":"solana_identity_missing"}
