from __future__ import annotations
from typing import Any, Dict, List

class AgentMesh:
    """138: dynamic specialist-agent collaboration and handoff."""

    def assign(self, tasks: List[Dict[str, Any]], agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for task in tasks:
            required = set(task.get("required_capabilities", []))
            candidates = []
            for agent in agents:
                caps = set(agent.get("capabilities", []))
                coverage = len(required & caps)
                reliability = float(agent.get("reliability", 0))
                load = float(agent.get("load", 0))
                score = coverage * 10 + reliability - load
                candidates.append((score, agent))
            candidates.sort(key=lambda x: x[0], reverse=True)
            chosen = candidates[0][1] if candidates else None
            out.append({
                **task,
                "assigned_agent": chosen.get("name") if chosen else None,
                "delegation_autonomous": True,
            })
        return out
