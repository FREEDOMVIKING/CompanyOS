class FeedbackIntelligenceEngine:
    def summarize(self, feedback):
        themes={}
        for f in feedback or []:
            theme=f.get("theme","other"); themes[theme]=themes.get(theme,0)+1
        ranked=sorted(themes.items(),key=lambda x:x[1],reverse=True)
        return {"themes":[{"theme":k,"count":v} for k,v in ranked],"top_theme":ranked[0][0] if ranked else None}
