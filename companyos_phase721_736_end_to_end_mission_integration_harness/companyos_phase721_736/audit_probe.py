from pathlib import Path

class AuditProbe:
    """726: confirm end-to-end audit files are receiving events."""

    FILES = [
        "unified_runtime_audit.jsonl",
        "venture_lifecycle_audit.jsonl",
        "strategic_learning_audit.jsonl",
        "ceo_scheduler_events.jsonl",
    ]

    def __init__(self, root):
        self.base=Path(root)/".companyos_runtime"

    def inspect(self):
        result={}
        for name in self.FILES:
            p=self.base/name
            result[name]={
                "exists":p.exists(),
                "size":p.stat().st_size if p.exists() else 0,
            }
        return result
