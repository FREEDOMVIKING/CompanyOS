class GrowthExperimentLoop:
    """1217-1228: select, run, and learn from bounded growth experiments."""
    def select(self, experiments, max_parallel=2):
        ranked=sorted(experiments or [],key=lambda x:(float(x.get("expected_impact",0))*float(x.get("confidence",0)))/(max(0.1,float(x.get("effort",1)))),reverse=True)
        return ranked[:int(max_parallel)]

    def evaluate(self, experiment_results):
        learnings=[]
        for r in experiment_results or []:
            success=float(r.get("observed_lift",0))>=float(r.get("success_threshold",0))
            learnings.append({
                "experiment":r.get("name"),
                "success":success,
                "action":"scale" if success else "stop_or_revise"
            })
        return learnings
