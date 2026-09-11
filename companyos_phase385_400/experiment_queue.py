import json
from pathlib import Path

class ExperimentQueue:
    """392: durable validation experiment queue."""

    def __init__(self, project_root):
        self.path = Path(project_root) / ".companyos_runtime" / "validation_experiments.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, experiments):
        self.path.write_text(json.dumps(experiments, indent=2, default=str), encoding="utf-8")
        return experiments

    def load(self):
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []
