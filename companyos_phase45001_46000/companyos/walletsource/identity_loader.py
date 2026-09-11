import json
from pathlib import Path

class VerifiedWalletIdentity:
    def __init__(self, root):
        self.root = Path(root)
        self.paths = [
            Path.home() / "companyos_runtime" / "wallet_identity.json",
            self.root / ".companyos_runtime" / "wallet_identity.json",
        ]

    def load(self):
        for p in self.paths:
            if not p.exists():
                continue
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if data.get("chain") == "solana" and data.get("public_address") and data.get("private_key_exposed") is False:
                return {"success":True,"status":"verified_wallet_identity_loaded","path":str(p),"chain":"solana","public_address":data["public_address"]}
        return {"success":False,"status":"verified_wallet_identity_missing"}
