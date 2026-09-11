class CapacityPlanner:
    def recommend(self, workload, workers, target_utilization=.7):
        workload=float(workload); workers=max(1,int(workers))
        current=workload/workers
        needed=max(1,round(workload/max(.1,float(target_utilization))))
        return {"current_load_per_worker":round(current,3),"recommended_workers":needed}
