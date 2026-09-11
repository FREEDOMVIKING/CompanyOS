class KPIEngine:
    def __init__(self,db):
        self.db=db

    def refresh(self):
        ventures=self.db.list_ventures()
        agents=self.db.list_agents()
        tasks=self.db.list_tasks(500)
        metrics={
            "ventures_total":len(ventures),
            "average_venture_score":round(sum(float(v.get("score",0) or 0) for v in ventures)/len(ventures),2) if ventures else 0,
            "agents_total":len(agents),
            "task_completion_rate":round(100*sum(t["status"]=="COMPLETED" for t in tasks)/len(tasks),2) if tasks else 100.0,
            "task_failures":sum(t["status"]=="FAILED" for t in tasks),
        }
        for k,v in metrics.items():
            self.db.metric("system","companyos",k,v,{})
        self.db.set_kv("kpis",metrics)
        return metrics
