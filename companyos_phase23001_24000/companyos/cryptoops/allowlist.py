import json
from pathlib import Path

class CryptoAllowlist:
    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "crypto_destination_allowlist.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return set()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return set()
        return set(data if isinstance(data, list) else [])

    def save(self, addresses):
        values = sorted(set(str(x).strip() for x in addresses if str(x).strip()))
        self.path.write_text(json.dumps(values, indent=2), encoding="utf-8")
        return values
