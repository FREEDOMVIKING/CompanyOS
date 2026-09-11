class ValidationHandoff:
    """797: build a validation-ready handoff packet from research evidence."""

    def build(self, mission, research_result):
        context = dict((mission or {}).get("context") or {})
        lifecycle = dict((research_result or {}).get("lifecycle_evidence") or {})
        packet = dict((research_result or {}).get("packet") or {})

        return {
            "venture_id": context.get("venture_id") or (context.get("venture_record") or {}).get("venture_id"),
            "source_mission_id": (mission or {}).get("mission_id"),
            "mission_type": "validation",
            "priority": min(1.0, float((mission or {}).get("priority", 0.8)) + 0.05),
            "context": {
                **context,
                "research_packet": packet,
                "research_confidence": lifecycle.get("research_confidence", packet.get("confidence", 0)),
                "validation_candidate_ready": bool(lifecycle.get("validation_candidate_ready")),
                "objective": "validate the highest-confidence customer/problem hypothesis using collected evidence",
            },
        }
