class MemoryConsolidator:
    def consolidate(self, events, max_items=20):
        events=list(events or [])
        themes={}
        for e in events:
            kind=e.get("kind","other")
            themes[kind]=themes.get(kind,0)+1
        important=sorted(events,key=lambda x:float((x.get("payload") or {}).get("importance",0.5)),reverse=True)[:max_items]
        return {"themes":themes,"important_events":important,"event_count":len(events)}
