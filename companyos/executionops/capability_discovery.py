from pathlib import Path

class CapabilityDiscovery:
    KEYWORDS = {
        "release": ("release", "deploy", "publisher", "launch"),
        "deployment": ("deploy", "deployment", "publish"),
        "marketing": ("marketing", "campaign", "social"),
        "coding": ("coding", "coder", "engineering", "builder"),
        "quality": ("quality", "verify", "test"),
        "operations": ("operations", "operator", "runtime"),
        "customer_success": ("customer_success", "support", "customer"),
        "finance": ("finance", "revenue", "accounting", "treasury"),
        "research": ("research", "market", "analysis"),
        "ceo": ("ceo", "strategy", "portfolio"),
    }

    def __init__(self, root):
        self.root = Path(root)

    def discover(self):
        found = {}
        for p in self.root.rglob("*.py"):
            if any(part in {".git","__pycache__","backups"} for part in p.parts):
                continue
            rel = str(p.relative_to(self.root))
            low = rel.lower()
            for cap, keys in self.KEYWORDS.items():
                if cap in found:
                    continue
                if any(k in low for k in keys):
                    found[cap] = rel
        return found

    def best_for(self, capability):
        return self.discover().get(capability)
