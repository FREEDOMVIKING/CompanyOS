from .persistent_runtime import PersistentRuntime
from .runtime_state import RuntimeState
from .runtime_health import RuntimeHealth
from companyos_phase689_704 import SafeMode

class RuntimeSupervisor:
    """718: supervised bounded runtime execution."""

    def __init__(self, root):
        self.root = root
        self.runtime = PersistentRuntime(root)
        self.state = RuntimeState(root)
        self.safe = SafeMode(root)

    def tick(self):
        state = self.state.load()
        safe = self.safe.status()
        state["safe_mode"] = bool(safe.get("enabled"))
        self.state.save(state)

        if safe.get("enabled"):
            return {
                "success": True,
                "status": "unified_runtime_safe_mode",
                "safe_mode": safe,
                "health": RuntimeHealth().evaluate(state),
            }

        result = self.runtime.run_once()
        return {
            **result,
            "health": RuntimeHealth().evaluate(self.state.load(), result),
        }
