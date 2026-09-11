class PortfolioLearningEngine:
    def learn(self, ventures):
        lessons=[]
        for v in ventures or []:
            if v.get("decision")=="SCALE":
                lessons.append({"venture_id":v["venture_id"],"lesson":"replicate_winning_pattern"})
            elif v.get("decision")=="RETIRE":
                lessons.append({"venture_id":v["venture_id"],"lesson":"avoid_or_reframe_pattern"})
            else:
                lessons.append({"venture_id":v["venture_id"],"lesson":"continue_measurement"})
        return lessons
