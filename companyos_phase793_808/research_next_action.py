class ResearchNextAction:
    """798: decide next research-loop action."""

    def decide(self, handoff_gate, research_result):
        completion = dict((research_result or {}).get("completion") or {})
        if handoff_gate.get("passed"):
            return "handoff_to_validation"
        if completion.get("reason") == "provider_chain_exhausted_partial_result":
            return "defer_and_research_later"
        return "continue_research"
