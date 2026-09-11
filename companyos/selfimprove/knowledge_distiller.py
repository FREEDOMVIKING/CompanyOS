class KnowledgeDistiller:
    def distill(self, events):
        themes={}
        for e in events or []:
            k=e.get("kind","other")
            themes[k]=themes.get(k,0)+1
        return {
            "themes":themes,
            "count":len(events or []),
            "lessons":[{"theme":k,"frequency":v} for k,v in sorted(themes.items(),key=lambda x:x[1],reverse=True)]
        }
