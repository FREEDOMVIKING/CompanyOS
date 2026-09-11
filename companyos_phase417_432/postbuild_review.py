class PostBuildReview:
    """425: summarize build evidence for CEO review."""

    def summarize(self, build_state, release_candidate, metrics):
        return {
            "build_status":build_state.get("status"),
            "cycles_used":build_state.get("cycle"),
            "release_candidate_ready":release_candidate.get("release_candidate_ready"),
            "metric_events_defined":metrics.get("event_count",0),
            "next":"portfolio_decision",
        }
