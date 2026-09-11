import json
from pathlib import Path


class VerifiedWalletIdentity:
    def __init__(self, root):
        self.root = Path(root)

        self.identity_paths = [
            self.root / "companyos_runtime" / "wallet_identity.json",
            self.root / ".companyos_runtime" / "wallet_identity.json",
        ]

        self.registry_paths = [
            self.root / "companyos" / "ceo_memory" / "treasury_wallet_registry.json",
            self.root / "ceo_memory" / "treasury_wallet_registry.json",
        ]

    def _load_identity_file(self):
        for p in self.identity_paths:
            if not p.exists():
                continue

            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue

            if (
                data.get("chain") == "solana"
                and data.get("public_address")
                and data.get("private_key_exposed") is False
            ):
                return {
                    "success": True,
                    "status": "verified_wallet_identity_loaded",
                    "path": str(p),
                    "source": "wallet_identity_file",
                    "chain": "solana",
                    "public_address": data["public_address"],
                    "private_key_exposed": False,
                }

        return None

    def _load_registry(self):
        for p in self.registry_paths:
            if not p.exists():
                continue

            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue

            wallets = data.get("wallets", [])

            if not isinstance(wallets, list):
                continue

            for wallet in wallets:
                if not isinstance(wallet, dict):
                    continue

                if (
                    str(wallet.get("chain", "")).lower() == "solana"
                    and wallet.get("address")
                    and wallet.get("enabled", True) is True
                ):
                    return {
                        "success": True,
                        "status": "verified_wallet_identity_loaded",
                        "path": str(p),
                        "source": "treasury_wallet_registry",
                        "chain": "solana",
                        "public_address": wallet["address"],
                        # Registry contains public identity only.
                        "private_key_exposed": False,
                    }

        return None

    def load(self):
        identity = self._load_identity_file()

        if identity:
            return identity

        registry_identity = self._load_registry()

        if registry_identity:
            return registry_identity

        return {
            "success": False,
            "status": "verified_wallet_identity_missing",
        }
