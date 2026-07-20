from __future__ import annotations
from pathlib import Path
from typing import Any, Dict

class ContractRepair:
    """271: normalize recovered objects into the CompanyOS files contract."""

    def normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return {"success": False, "reason": "recovered_payload_not_object", "files": {}}

        files = data.get("files")

        # Common alternate shapes produced by coding models.
        if not isinstance(files, dict):
            artifacts = data.get("artifacts")
            if isinstance(artifacts, list):
                converted = {}
                for item in artifacts:
                    if not isinstance(item, dict):
                        continue
                    path = item.get("path") or item.get("filename") or item.get("file")
                    content = item.get("content") or item.get("code")
                    if isinstance(path, str) and isinstance(content, str):
                        converted[path] = content
                files = converted

        if not isinstance(files, dict) or not files:
            return {
                "success": False,
                "reason": "files_missing_or_empty_after_recovery",
                "files": {},
            }

        safe = {}
        for rel, content in files.items():
            if not isinstance(rel, str) or not isinstance(content, str):
                return {
                    "success": False,
                    "reason": "invalid_file_entry",
                    "files": {},
                }
            p = Path(rel)
            if p.is_absolute() or ".." in p.parts:
                return {
                    "success": False,
                    "reason": f"unsafe_path:{rel}",
                    "files": {},
                }
            safe[str(p)] = content

        return {
            "success": True,
            "files": safe,
            "metadata": data.get("metadata", {}),
        }
