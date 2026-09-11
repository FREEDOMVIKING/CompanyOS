from __future__ import annotations

class SourcePolicy:
    """338: prioritize evidence quality and diversity over sheer volume."""

    def evaluate(self, source):
        priority = float(source.get("priority", 0.5))
        enabled = bool(source.get("enabled", True))
        has_url = bool(source.get("url"))
        category = source.get("category") or "uncategorized"
        return {
            "usable": enabled and has_url,
            "priority": priority,
            "category": category,
            "preferred": enabled and has_url and priority >= 0.7,
        }
