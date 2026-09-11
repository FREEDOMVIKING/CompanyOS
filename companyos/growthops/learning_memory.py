class LearningMemory:
    def summarize(self, experiments):
        wins=[e for e in experiments or [] if e.get("action")=="scale"]
        losses=[e for e in experiments or [] if e.get("action")=="stop_or_redesign"]
        return {
            "wins":len(wins),"losses":len(losses),
            "lessons":[{"experiment":e.get("name"),"lesson":"repeat_or_expand"} for e in wins]+
                      [{"experiment":e.get("name"),"lesson":"revise_or_stop"} for e in losses]
        }
