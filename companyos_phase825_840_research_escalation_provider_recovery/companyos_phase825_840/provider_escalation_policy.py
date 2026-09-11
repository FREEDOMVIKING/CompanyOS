class ProviderEscalationPolicy:
    """826: decide retry, switch provider, reformulate, or defer."""

    def decide(self, failure, provider_attempts, total_attempts, max_total=8):
        if failure.get("kind") == "none":
            return "continue_evidence_processing"
        if total_attempts >= max_total:
            return "defer"
        if failure.get("kind") in ("rate_limited","not_configured"):
            return "switch_provider"
        if provider_attempts >= 2:
            return "reformulate_and_switch"
        return "retry_provider"
