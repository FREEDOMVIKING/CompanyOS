from .util import stable_id, now

class InternalExecutor:
    def __init__(self,db):
        self.db=db

    def seed(self):
        created=0
        agents=self.db.list_agents()
        for c in self.db.list_companies():
            ca=[a for a in agents if a.get("company_id")==c["company_id"]]
            lead=ca[0]["agent_id"] if ca else None
            for kind,title,prio in [
                ("executive_review","Run executive company review",94),
                ("memory_review","Extract reusable company lessons",88),
                ("optimization_review","Review workload and agent fit",86),
            ]:
                tid=stable_id("v9-task",c["company_id"],kind)
                self.db.add_task(tid,c["company_id"],kind,title,prio,lead,{"company_name":c["name"]})
                created+=1
        return created

    def run(self,limit=80):
        count=0
        for t in self.db.next_tasks(limit):
            self.db.task_state(t["task_id"],"RUNNING",1)
            self.db.event("task.started",t.get("agent_id") or "executor",{"task_id":t["task_id"]},t.get("company_id"))
            try:
                result={"task_id":t["task_id"],"title":t["title"],"status":"COMPLETED",
                        "company_id":t.get("company_id"),"external_side_effects":False,"completed_at":now()}
                self.db.task_state(t["task_id"],"COMPLETED")
                self.db.event("task.completed",t.get("agent_id") or "executor",result,t.get("company_id"))
            except Exception as e:
                self.db.task_state(t["task_id"],"FAILED")
                self.db.event("task.failed","executor",{"task_id":t["task_id"],"error":str(e)})
            count+=1
        return count
