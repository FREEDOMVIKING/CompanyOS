import hashlib

class MissionDeduplicator:
    """812: collapse semantically duplicate queued missions."""

    def _key(self, mission):
        ctx = dict((mission or {}).get("context") or {})
        venture = ctx.get("venture_id") or (ctx.get("venture_record") or {}).get("venture_id") or ""
        objective = ctx.get("objective") or ctx.get("research_goal") or ctx.get("next_action") or ""
        raw = f"{mission.get('mission_type')}|{venture}|{objective}".lower().strip()
        return hashlib.sha256(raw.encode()).hexdigest()

    def dedupe(self, missions):
        kept, dropped, seen = [], [], set()
        for m in missions or []:
            key = self._key(m)
            if key in seen:
                dropped.append(m)
            else:
                seen.add(key)
                kept.append(m)
        return {"kept": kept, "dropped": dropped}
