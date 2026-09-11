class CircuitBreaker:
    def evaluate(self, state, failure_threshold=3):
        failures=int((state or {}).get("consecutive_failures",0))
        open_=failures>=int(failure_threshold)
        return {
            "open":open_,
            "allowed":not open_,
            "action":"block_and_probe_later" if open_ else "allow"
        }
