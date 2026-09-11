class AutonomousGrowthLoop:
    def choose(self, channels, max_parallel=3):
        ranked=sorted(channels or [],key=lambda x:float(x.get("channel_score",0)),reverse=True)
        return ranked[:int(max_parallel)]

    def evaluate(self, results):
        out=[]
        for r in results or []:
            success=float(r.get("observed_lift",0))>=float(r.get("success_threshold",0))
            out.append({
                "name":r.get("name"),
                "success":success,
                "action":"scale" if success else "revise_or_stop"
            })
        return out
