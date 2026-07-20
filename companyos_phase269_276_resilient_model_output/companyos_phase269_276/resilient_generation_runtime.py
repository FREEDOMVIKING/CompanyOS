from __future__ import annotations
from pathlib import Path
from .resilient_openrouter_adapter import ResilientOpenRouterAdapter

class ResilientGenerationRuntime:
    """276: status surface for resilient autonomous generation."""

    def __init__(self, project_root):
        self.root = Path(project_root).resolve()
        self.adapter = ResilientOpenRouterAdapter()

    def status(self):
        return {
            "success": True,
            "status": "phase276_resilient_generation_runtime_ready",
            "openrouter_key_loaded": self.adapter.configured,
            "json_recovery": True,
            "markdown_fence_recovery": True,
            "near_json_recovery": True,
            "contract_repair": True,
            "automatic_format_retry": True,
            "autonomous_builder_bridge_connected": True,
            "autonomy_mode": "high",
        }
