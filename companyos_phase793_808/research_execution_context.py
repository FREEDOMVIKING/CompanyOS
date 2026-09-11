class ResearchExecutionContext:
    """793: normalize live research mission context for multi-provider execution."""

    def build(self, mission):
        context = dict((mission or {}).get("context") or {})
        venture = dict(context.get("venture_record") or {})
        return {
            "mission_id": (mission or {}).get("mission_id"),
            "venture_id": context.get("venture_id") or venture.get("venture_id"),
            "query": (
                context.get("query")
                or context.get("objective")
                or context.get("next_action")
                or venture.get("problem")
                or "collect targeted market evidence"
            ),
            "query_type": context.get("query_type") or "market",
            "preferred_provider": context.get("provider_hint") or "github",
            "attempts": int((mission or {}).get("attempts", 0)),
            "raw_context": context,
        }
