from __future__ import annotations

class ConnectionContract:
    """239: validate external coder output before files touch a workspace."""

    def validate(self, payload):
        if not isinstance(payload, dict):
            return {"valid": False, "reason": "payload_not_object"}
        files = payload.get("files")
        if not isinstance(files, dict) or not files:
            return {"valid": False, "reason": "files_missing_or_empty"}
        for path, content in files.items():
            if not isinstance(path, str) or not isinstance(content, str):
                return {"valid": False, "reason": "invalid_file_entry"}
            if path.startswith("/") or ".." in path.split("/"):
                return {"valid": False, "reason": f"unsafe_path:{path}"}
        return {"valid": True, "file_count": len(files)}
