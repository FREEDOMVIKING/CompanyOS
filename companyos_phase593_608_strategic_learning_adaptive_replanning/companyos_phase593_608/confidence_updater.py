class ConfidenceUpdater:
    """603: update confidence without pretending certainty."""

    def update(self, current, lessons):
        confidence = float(current if current is not None else 0.5)
        for lesson in lessons:
            if str(lesson).startswith("stage_advanced:"):
                confidence += 0.08
            elif lesson in ("weak_activation","weak_retention","no_revenue_signal","quality_failure"):
                confidence -= 0.10
        return round(max(0.05,min(0.95,confidence)),3)
