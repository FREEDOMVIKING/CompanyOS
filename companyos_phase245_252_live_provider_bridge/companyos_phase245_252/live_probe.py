from __future__ import annotations

class LiveProbe:
    """248: verify a real provider can return the CompanyOS file contract."""

    def run(self, adapter):
        payload = {
            "task": "Return a tiny Python capability as JSON files only.",
            "build_spec": {
                "capability": "live_provider_probe",
                "module_name": "generated_live_provider_probe",
            },
            "required_files": [
                "generated_live_provider_probe/__init__.py",
                "generated_live_provider_probe/core.py",
                "tests/test_generated_live_provider_probe.py",
            ],
        }
        result = adapter.invoke(payload)
        return {
            "success": bool(result.get("success")),
            "file_count": len(result.get("files", {})),
            "result": result,
        }
