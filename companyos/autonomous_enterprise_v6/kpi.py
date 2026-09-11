class EnterpriseKPI:
    def __init__(self,db):
        self.db=db

    def refresh(self):
        companies=self.db.list_companies()
        agents=self.db.list_agents()
        tasks=self.db.list_tasks(600)
        metrics={
            "companies_total":len(companies),
            "average_company_priority":round(sum(float(c.get("priority",0) or 0) for c in companies)/len(companies),2) if companies else 0,
            "agents_total":len(agents),
            "task_completion_rate":round(100*sum(t["status"]=="COMPLETED" for t in tasks)/len(tasks),2) if tasks else 100.0,
            "failed_tasks":sum(t["status"]=="FAILED" for t in tasks),
        }
        self.db.set_kv("enterprise_kpis",metrics)
        for k,v in metrics.items():
            self.db.metric("enterprise","companyos",k,v,{})
        return metrics
