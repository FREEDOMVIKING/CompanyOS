class MemoryConsolidationEngine:
    def consolidate(self, memories, limit=25):
        memories=list(memories or [])
        themes={}
        for m in memories:
            themes[m.get("kind","other")]=themes.get(m.get("kind","other"),0)+1
        important=sorted(
            memories,
            key=lambda x:float(x.get("importance",.5)),
            reverse=True
        )[:int(limit)]
        return {
            "memory_count":len(memories),
            "themes":themes,
            "important_memories":important,
            "summary":"consolidated_for_next_decision_cycle"
        }
