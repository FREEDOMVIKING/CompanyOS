from __future__ import annotations
from pathlib import Path
from .model_router import ModelRouter
from .openrouter_adapter import OpenRouterCoderAdapter
from .execution_budget import ExecutionBudget

class LiveIntelligenceRuntime:
    """260: status surface for CompanyOS's real autonomous coding brain."""

    def __init__(self, project_root):
        self.root = Path(project_root).resolve()
        self.adapter = OpenRouterCoderAdapter()
        self.router = ModelRouter()
        self.budget = ExecutionBudget()

    def status(self):
        return {
            "success": True,
            "status": "phase260_live_intelligence_builder_ready",
            "openrouter_key_loaded": self.adapter.configured,
            "model_routing": self.router.routing_plan(),
            "execution_limits": self.budget.limits(),
            "self_build_pipeline_connected": True,
            "autonomy_mode": "high",
        }
