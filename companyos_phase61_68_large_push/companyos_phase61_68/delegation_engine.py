from __future__ import annotations
from typing import Any, Dict, List

class DelegationEngine:
    """Phase 66: assign tasks to specialist agents using capability matching."""
    def assign(self, tasks: List[Dict[str, Any]], agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        output = []
        for task in tasks:
            required = set(task.get("required_capabilities", []))
            best = None
            best_score = -1
            for agent in agents:
                caps = set(agent.get("capabilities", []))
                score = len(required & caps)
                if required and not required.issubset(caps):
                    score -= 100
                if score > best_score:
                    best_score = score
                    best = agent
            output.append({
                **task,
                "assigned_agent": best.get("name") if best and best_score >= 0 else None,
                "assignment_score": best_score,
            })
        return output
