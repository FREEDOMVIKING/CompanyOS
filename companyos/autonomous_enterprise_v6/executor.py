from .util import now

class InternalExecutor:
    def __init__(self,db):
        self.db=db

    def run(self,limit=40):
        processed=0
        for t in self.db.next_tasks(limit):
            self.db.task_state(t["task_id"],"RUNNING",1)
            try:
                result={
                    "task_id":t["task_id"],
                    "company_id":t.get("company_id"),
                    "agent_id":t.get("agent_id"),
                    "title":t["title"],
                    "status":"COMPLETED",
                    "external_side_effects":False,
                    "completed_at":now()
                }
                self.db.event("task.completed",t.get("agent_id") or "executor",result,target=t.get("company_id"))
                if t.get("agent_id"): self.db.agent_result(t["agent_id"],True)
                self.db.task_state(t["task_id"],"COMPLETED")
            except Exception as e:
                self.db.event("task.failed","executor",{"task_id":t["task_id"],"error":str(e)})
                if t.get("agent_id"): self.db.agent_result(t["agent_id"],False)
                self.db.task_state(t["task_id"],"FAILED")
            processed+=1
        return processed
