from __future__ import annotations
from typing import Any, Dict, Iterable

class AgentRouter:
    """Phase 55: deterministic role routing for internal tasks."""
    DEFAULT = {
        "research": "research_agent",
        "strategy": "strategy_agent",
        "build": "builder_agent",
        "growth": "growth_agent",
        "review": "ceo_agent",
        "operations": "operations_agent",
    }

    def route(self, task: Dict[str, Any]) -> str:
        category = str(task.get("category", "")).lower()
        title = str(task.get("title", "")).lower()
        text = f"{category} {title}"
        for key, role in self.DEFAULT.items():
            if key in text:
                return role
        return "ceo_agent"
