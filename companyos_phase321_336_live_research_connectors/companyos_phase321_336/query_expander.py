from __future__ import annotations

class QueryExpander:
    """330: expand research themes for search-capable future adapters."""

    def expand(self, theme):
        theme = str(theme).strip()
        return [
            f"{theme} customer complaints",
            f"{theme} manual workflow pain",
            f"{theme} pricing alternatives",
            f"{theme} software competitors",
            f"{theme} willingness to pay",
        ]
