class QueueDrainMetrics:
    """820: prove queue is draining rather than growing."""

    def compare(self, before, after):
        b = int((before or {}).get("count",0))
        a = int((after or {}).get("count",0))
        return {
            "before_count": b,
            "after_count": a,
            "delta": a - b,
            "drained": a < b,
            "non_growing": a <= b,
        }
