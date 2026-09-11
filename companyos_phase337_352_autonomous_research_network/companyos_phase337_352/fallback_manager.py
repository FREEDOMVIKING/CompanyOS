from __future__ import annotations

class FallbackManager:
    """339: choose alternate configured sources when preferred sources fail."""

    def choose(self, sources, failed_names=None):
        failed = set(failed_names or [])
        usable = [
            s for s in sources
            if s.get("enabled", True) and s.get("name") not in failed
        ]
        return sorted(usable, key=lambda s: float(s.get("priority", 0.5)), reverse=True)
