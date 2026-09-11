class EventRouter:
    """501: map system events into scheduler actions."""

    MAP = {
        "new_evidence": "reprioritize",
        "validation_metrics_ready": "resume_blocked",
        "operations_metrics_ready": "resume_blocked",
        "mission_failed": "review_retry",
        "venture_created": "enqueue_build",
        "release_candidate_ready": "enqueue_operations",
        "portfolio_review_due": "enqueue_portfolio",
    }

    def route(self, event_type):
        return self.MAP.get(event_type, "record_only")
