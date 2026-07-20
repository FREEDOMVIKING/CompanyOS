from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


class AutonomousCodeGenerator:
    """215: materialize model-generated files into an isolated workspace."""

    def generate(self, adapter, workspace: str | Path, build_spec: Dict[str, Any], context=None):
        workspace = Path(workspace)
        prompt = {
            "task": "Implement the missing CompanyOS capability.",
            "build_spec": build_spec,
            "context": context or {},
            "constraints": [
                "write only relative project files",
                "include tests",
                "do not modify backups",
                "keep changes reversible",
            ],
        }
        result = adapter.generate(prompt)
        if not result.get("success"):
            return {**result, "written_files": []}

        written = []
        for rel, content in result.get("files", {}).items():
            rel_path = Path(rel)
            if rel_path.is_absolute() or ".." in rel_path.parts:
                return {
                    "success": False,
                    "reason": f"unsafe_generated_path:{rel}",
                    "written_files": written,
                }
            target = workspace / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(content), encoding="utf-8")
            written.append(str(rel_path))

        return {
            "success": True,
            "written_files": written,
            "metadata": result.get("metadata", {}),
        }
