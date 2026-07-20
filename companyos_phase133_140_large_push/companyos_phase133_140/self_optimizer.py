from __future__ import annotations
from typing import Any, Dict

class SelfOptimizer:
    """137: propose and auto-apply reversible internal optimizations."""

    SAFE_AUTO = {
        "prompt_tuning",
        "task_routing",
        "retry_policy",
        "cache_strategy",
        "test_coverage",
        "internal_workflow",
    }

    def evaluate(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        kind = str(proposal.get("kind", "unknown"))
        reversible = bool(proposal.get("reversible", True))
        bounded = bool(proposal.get("bounded", True))
        auto_apply = kind in self.SAFE_AUTO and reversible and bounded
        return {
            "auto_apply": auto_apply,
            "approval_required": not auto_apply,
            "kind": kind,
            "reversible": reversible,
            "bounded": bounded,
        }
