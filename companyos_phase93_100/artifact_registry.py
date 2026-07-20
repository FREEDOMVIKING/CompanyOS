from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List

class ArtifactRegistry:
    """95: track generated internal artifacts and lineage."""
    def __init__(self):
        self.items: List[Dict[str, Any]] = []

    def register(self, kind: str, title: str, source_task_id=None, metadata=None):
        item = {
            "artifact_id": f"art-{len(self.items)+1:06d}",
            "kind": kind,
            "title": title,
            "source_task_id": source_task_id,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.items.append(item)
        return item
