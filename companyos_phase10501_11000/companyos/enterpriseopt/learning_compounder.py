class LearningCompounder:
    def compound(self, lessons):
        themes={}
        for l in lessons or []:
            theme=l.get("theme","other")
            themes[theme]=themes.get(theme,0)+float(l.get("weight",1))
        ranked=sorted(themes.items(),key=lambda x:x[1],reverse=True)
        return {
            "ranked_lessons":[{"theme":k,"weight":v} for k,v in ranked],
            "top_focus":ranked[0][0] if ranked else None
        }
