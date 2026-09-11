class VentureLifecycleSupervisor:
    STAGES=["discover","research","validate","build","launch","operate","optimize","retire"]

    def evaluate(self, venture):
        stage=venture.get("stage","discover")
        health=venture.get("health","healthy")
        score=float(venture.get("score",0))
        if health!="healthy":
            return {"venture_id":venture.get("venture_id"),"action":"repair","stage":stage}
        if stage=="operate" and score>=0.75:
            return {"venture_id":venture.get("venture_id"),"action":"scale","stage":"optimize"}
        if score<0.25 and stage in ("operate","optimize"):
            return {"venture_id":venture.get("venture_id"),"action":"retire_candidate","stage":"retire"}
        idx=self.STAGES.index(stage) if stage in self.STAGES else 0
        next_stage=self.STAGES[min(idx+1,len(self.STAGES)-1)]
        return {"venture_id":venture.get("venture_id"),"action":"advance","stage":next_stage}
