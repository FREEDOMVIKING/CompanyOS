from __future__ import annotations

class CompetitorPressure:
    """344: summarize competitive intensity from collected evidence."""

    def score(self, signals):
        count = len(signals)
        if count == 0:
            level = "unknown"
        elif count <= 2:
            level = "low_signal"
        elif count <= 6:
            level = "moderate"
        else:
            level = "high"
        return {"signal_count": count, "pressure_level": level}
