class RecoveryProbe:
    """731: evaluate whether runtime remains recoverable after a test cycle."""

    def evaluate(self, state, queue):
        return {
            "recoverable":int(state.get("consecutive_failures",0)) < 3,
            "consecutive_failures":int(state.get("consecutive_failures",0)),
            "queue_count":int(queue.get("count",0)),
        }
