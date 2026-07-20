from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List

class ContextPackager:
    """221: package bounded live-code context for a coding/reasoning model."""

    EXCLUDE = {".git","backups",".venv","venv","__pycache__",".pytest_cache","node_modules"}

    def collect(self, project_root, max_files=40, max_chars=120000):
        root=Path(project_root)
        files=[]
        total=0
        for p in sorted(root.rglob("*.py")):
            rel=p.relative_to(root)
            if any(part in self.EXCLUDE for part in rel.parts):
                continue
            try:
                text=p.read_text(encoding="utf-8")
            except Exception:
                continue
            if total+len(text)>max_chars:
                break
            files.append({"path":str(rel),"content":text})
            total+=len(text)
            if len(files)>=max_files:
                break
        return {"files":files,"file_count":len(files),"char_count":total}
