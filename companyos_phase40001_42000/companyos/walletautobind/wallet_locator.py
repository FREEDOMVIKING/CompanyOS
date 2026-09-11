from pathlib import Path

class ExistingWalletLocator:
    CANDIDATE_NAMES = (
        "wallet_port.py",
        "wallet_manager.py",
        "solana_wallet.py",
        "crypto_wallet.py",
        "multichain_execution_adapter.py",
    )
    TOKENS = (
        "wallet_address",
        "public_key",
        "solana",
        "sign_transaction",
        "send_transaction",
        "base58",
        "keypair",
        "multichain_signer_command",
    )

    def __init__(self, root):
        self.root = Path(root)

    def scan(self):
        results = []
        for p in self.root.rglob("*.py"):
            if any(part in {".git","__pycache__","backups"} for part in p.parts):
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore").lower()
            except Exception:
                continue

            score = 0
            if p.name.lower() in self.CANDIDATE_NAMES:
                score += 6
            for token in self.TOKENS:
                if token in text:
                    score += 1

            if score >= 4:
                results.append({
                    "path": str(p),
                    "relative_path": str(p.relative_to(self.root)),
                    "name": p.name,
                    "score": score,
                })
        return sorted(results, key=lambda x: (-x["score"], x["relative_path"]))

    def best(self):
        rows = self.scan()
        return rows[0] if rows else None
