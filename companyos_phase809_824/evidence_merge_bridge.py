class EvidenceMergeBridge:
    """815: merge recovered evidence into mission context."""

    def apply(self, mission, recovery_result):
        m = dict(mission or {})
        ctx = dict(m.get("context") or {})
        cycle = dict((recovery_result or {}).get("research_cycle") or {})
        research = dict(cycle.get("research_result") or {})
        packet = dict(research.get("packet") or {})
        evidence = list(research.get("evidence") or packet.get("evidence") or [])

        existing = list(ctx.get("evidence") or [])
        by_key = {}
        for item in existing + evidence:
            if isinstance(item, dict):
                key = item.get("url") or item.get("id") or str(item)
            else:
                key = str(item)
            by_key[key] = item

        ctx["evidence"] = list(by_key.values())
        if packet:
            ctx["research_packet"] = packet
        m["context"] = ctx
        return m
