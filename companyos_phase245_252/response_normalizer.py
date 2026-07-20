from __future__ import annotations
import json

class ResponseNormalizer:
    """246: normalize provider output into CompanyOS {files:{path:content}} contract."""

    def normalize(self, data):
        if isinstance(data, dict) and isinstance(data.get("files"), dict):
            return {"success": bool(data["files"]), "files": data["files"], "metadata": data.get("metadata", {})}

        text = None
        if isinstance(data, dict):
            text = data.get("text") or data.get("output") or data.get("content")
        elif isinstance(data, str):
            text = data

        if not text:
            return {"success": False, "reason": "no_usable_provider_output", "files": {}}

        try:
            parsed = json.loads(text)
        except Exception:
            return {"success": False, "reason": "provider_output_not_json", "files": {}}

        files = parsed.get("files", {}) if isinstance(parsed, dict) else {}
        return {"success": isinstance(files, dict) and bool(files), "files": files, "metadata": parsed.get("metadata", {}) if isinstance(parsed, dict) else {}}
