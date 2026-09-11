class RecoveryManager:
    def __init__(self,db):
        self.db=db

    def health(self):
        modules=self.db.list_modules()
        bad=[m for m in modules if not m.get("healthy")]
        pct=round(100*(len(modules)-len(bad))/len(modules),1) if modules else 100.0
        recs=[]
        if bad:
            recs.append(f"Review {len(bad)} unhealthy imported module states.")
        if pct<90:
            recs.append("Keep external execution disabled until health improves.")
        out={"health_percent":pct,"modules_total":len(modules),"unhealthy_modules":len(bad),"recommendations":recs}
        self.db.set_kv("health_report",out)
        return out
