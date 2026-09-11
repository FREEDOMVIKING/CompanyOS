from __future__ import annotations

class SourceScheduler:
    """332: prioritize enabled sources by configured priority."""

    def order(self, sources):
        return sorted(
            [s for s in sources if s.get("enabled", True)],
            key=lambda s: float(s.get("priority", 0.5)),
            reverse=True,
        )
