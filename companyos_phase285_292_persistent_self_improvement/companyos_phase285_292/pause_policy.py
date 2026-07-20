from __future__ import annotations

class PausePolicy:
    """287: pause persistent loop on repeated failures or manual pause."""

    def evaluate(self, state, failure_state, max_failures=3):
        if state.get("paused"):
            return {"pause": True, "reason": "manual_pause"}
        if int(failure_state.get("consecutive_failures", 0)) >= int(max_failures):
            return {"pause": True, "reason": "repeated_failures"}
        return {"pause": False, "reason": None}
