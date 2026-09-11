class StrategyEvolver:
    def evolve(self, current_strategy, lessons):
        strategy=dict(current_strategy or {})
        strategy["revision"]=int(strategy.get("revision",0))+1
        strategy["lessons_applied"]=[x.get("theme") for x in (lessons or {}).get("lessons",[])[:5]]
        return strategy
