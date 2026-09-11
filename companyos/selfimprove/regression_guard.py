class RegressionGuard:
    def compare(self, baseline, candidate, tolerance=.05):
        regressions={}
        if candidate.get("success_rate",0) < baseline.get("success_rate",0)-tolerance:
            regressions["success_rate"]="regressed"
        if candidate.get("latency",0) > baseline.get("latency",0)*(1+tolerance):
            regressions["latency"]="regressed"
        if candidate.get("cost_per_cycle",0) > baseline.get("cost_per_cycle",0)*(1+tolerance):
            regressions["cost_per_cycle"]="regressed"
        return {"passed":not regressions,"regressions":regressions}
