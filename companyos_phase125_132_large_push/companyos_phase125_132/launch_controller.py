from __future__ import annotations
from typing import Any, Dict

class LaunchController:
    """130: autonomous internal/local launch; gated consequential external launch."""

    def evaluate(self, launch: Dict[str, Any]) -> Dict[str, Any]:
        scope = str(launch.get("scope", "internal"))
        reversible = bool(launch.get("reversible", True))
        bounded = bool(launch.get("bounded", True))

        autonomous = scope in {"internal", "local", "sandbox", "staging"} and reversible and bounded

        return {
            "autonomous_launch_allowed": autonomous,
            "approval_required": not autonomous,
            "scope": scope,
            "reversible": reversible,
            "bounded": bounded,
        }
