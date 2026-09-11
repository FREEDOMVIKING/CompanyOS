import json
from pathlib import Path

class CandidateStore:
    """529: persistent store for scored opportunity candidates."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "quality_candidates.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def save(self, candidates):
        self.path.write_text(json.dumps(candidates, indent=2, default=str), encoding="utf-8")
        return candidates
