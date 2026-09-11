class LifecycleHealth:
    """591: lifecycle integrity checks."""

    def evaluate(self, records):
        invalid = [
            r for r in records
            if not r.get("venture_id") or not r.get("stage")
        ]
        stalled = [
            r.get("venture_id") for r in records
            if int(r.get("stagnant_cycles",0)) >= 3
        ]
        return {
            "healthy":not invalid,
            "invalid_records":invalid,
            "stalled_ventures":stalled,
            "venture_count":len(records),
        }
