class VentureCoordinator:
    def coordinate(self, ventures):
        actions=[]
        for v in ventures or []:
            score=float(v.get("score",0))
            health=v.get("health","healthy")
            if health!="healthy":
                action="repair"
            elif score>=0.75:
                action="scale"
            elif score>=0.5:
                action="optimize"
            elif score<0.3:
                action="retire_candidate"
            else:
                action="observe"
            actions.append({"venture_id":v.get("venture_id"),"action":action})
        return actions
