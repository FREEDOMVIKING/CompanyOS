class RecoveryAdvisor:
    def __init__(self,db):
        self.db=db

    def inspect(self):
        agents=self.db.list_agents()
        tasks=self.db.list_tasks(600)
        failed=[t for t in tasks if t["status"]=="FAILED"]
        weak_agents=[a for a in agents if float(a.get("score",50) or 50)<70]
        recs=[]
        if failed: recs.append(f"Review {len(failed)} failed enterprise tasks.")
        if weak_agents: recs.append(f"Review {len(weak_agents)} low-scoring agents.")
        if not recs: recs.append("No enterprise recovery action required.")
        out={
            "failed_tasks":len(failed),
            "low_scoring_agents":len(weak_agents),
            "recommendations":recs
        }
        self.db.set_kv("recovery_report",out)
        return out
