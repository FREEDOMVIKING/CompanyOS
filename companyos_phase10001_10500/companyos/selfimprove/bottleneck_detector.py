class BottleneckDetector:
    def detect(self, baseline, thresholds=None):
        t=thresholds or {}
        issues=[]
        if baseline.get("success_rate",1)<float(t.get("min_success_rate",.95)):
            issues.append({"kind":"reliability","severity":"high"})
        if baseline.get("latency",0)>float(t.get("max_latency",5)):
            issues.append({"kind":"latency","severity":"medium"})
        if baseline.get("cost_per_cycle",0)>float(t.get("max_cost_per_cycle",10)):
            issues.append({"kind":"cost","severity":"medium"})
        if baseline.get("recovery_rate",1)<float(t.get("min_recovery_rate",.9)):
            issues.append({"kind":"recovery","severity":"high"})
        return issues
