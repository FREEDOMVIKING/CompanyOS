from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any, Dict

class CodeContract:
    """254: normalize model output into a safe CompanyOS files contract."""

    def _extract_json_text(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
            text = re.sub(r"\s*```$", "", text)
        try:
            json.loads(text)
            return text
        except Exception:
            pass
        start, end = text.find("{"), text.rfind("}")
        return text[start:end+1] if start >= 0 and end > start else text

    def normalize(self, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict) and isinstance(payload.get("files"), dict):
            data = payload
        else:
            text = payload if isinstance(payload, str) else ""
            if isinstance(payload, dict):
                text = payload.get("text") or payload.get("content") or payload.get("output") or ""
            try:
                data = json.loads(self._extract_json_text(str(text)))
            except Exception as exc:
                return {"success": False, "reason": f"invalid_json_contract:{type(exc).__name__}", "files": {}}

        files = data.get("files", {}) if isinstance(data, dict) else {}
        if not isinstance(files, dict) or not files:
            return {"success": False, "reason": "files_missing_or_empty", "files": {}}

        safe = {}
        for rel, content in files.items():
            if not isinstance(rel, str) or not isinstance(content, str):
                return {"success": False, "reason": "invalid_file_entry", "files": {}}
            p = Path(rel)
            if p.is_absolute() or ".." in p.parts:
                return {"success": False, "reason": f"unsafe_path:{rel}", "files": {}}
            safe[str(p)] = content

        return {"success": True, "files": safe, "metadata": data.get("metadata", {})}
