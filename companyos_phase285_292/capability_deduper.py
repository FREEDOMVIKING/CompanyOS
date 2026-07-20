from __future__ import annotations

class CapabilityDeduper:
    """289: prevent repeatedly rebuilding the same capability without reason."""

    def should_skip(self, proposal, state):
        improvement = (proposal or {}).get("improvement")
        last_capability = state.get("last_capability")
        if not improvement or not last_capability:
            return False
        return improvement == last_capability
