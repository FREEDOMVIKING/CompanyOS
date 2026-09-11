class HealthManager:
    def __init__(self, db, bus):
        self.db=db
        self.bus=bus

    def inspect(self):
        modules=self.db.list_modules()
        plugins=self.db.list_plugins()
        unhealthy=[m for m in modules if not m.get("healthy")]
        bad_plugins=[p for p in plugins if p.get("health") not in ("OK","UNKNOWN")]
        total=len(modules)
        healthy=total-len(unhealthy)
        pct=round((healthy/total*100),1) if total else 100.0
        recs=[]
        if unhealthy:
            recs.append(f"Review {len(unhealthy)} unhealthy legacy/module states.")
        if bad_plugins:
            recs.append(f"Review {len(bad_plugins)} unhealthy plugins.")
        if pct < 90:
            recs.append("Run migration + module audit before enabling any new external adapters.")
        report={"health_percent":pct,"modules_total":total,"unhealthy_modules":len(unhealthy),
                "plugins_total":len(plugins),"unhealthy_plugins":len(bad_plugins),"recommendations":recs}
        self.bus.publish("health.report","health_manager",report)
        self.db.set_kv("health_report",report)
        return report
