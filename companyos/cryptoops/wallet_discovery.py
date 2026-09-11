from pathlib import Path

class WalletDiscovery:
    CANDIDATE_NAMES = {
        "wallet.py","wallet_port.py","wallet_adapter.py","wallet_manager.py",
        "solana_wallet.py","evm_wallet.py","crypto_wallet.py","wallet_bridge.py"
    }

    KEYWORDS = (
        "base58","solana","evm","wallet_address","private_key",
        "sign_transaction","send_transaction","wallet_port"
    )

    def __init__(self, root):
        self.root = Path(root)

    def scan(self):
        results = []
        for p in self.root.rglob("*.py"):
            if any(part in {".git","__pycache__","backups"} for part in p.parts):
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            score = 0
            lower = text.lower()
            if p.name.lower() in self.CANDIDATE_NAMES:
                score += 4
            for k in self.KEYWORDS:
                if k in lower:
                    score += 1

            if score >= 3:
                results.append({
                    "path": str(p),
                    "score": score,
                    "name": p.name,
                })

        return sorted(results, key=lambda x: (-x["score"], x["path"]))
