import json
from pathlib import Path
from hashlib import sha256

class DuplicatePaymentGuard:
    def __init__(self, root):
        self.path = Path(root)/".companyos_runtime"/"payment_fingerprints.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self):
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text())
        except Exception:
            return {}

    def fingerprint(self, source, destination, amount, token=None, memo=""):
        raw = f"{source}|{destination}|{amount}|{token or ''}|{memo}"
        return sha256(raw.encode()).hexdigest()

    def seen(self, fp):
        return fp in self._load()

    def record(self, fp, metadata=None):
        data = self._load()
        data[fp] = metadata or {}
        self.path.write_text(json.dumps(data, indent=2))
