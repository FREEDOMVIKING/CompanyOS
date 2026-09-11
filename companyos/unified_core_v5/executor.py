from .util import now

class InternalExecutor:
    def __init__(self,db):
        self.db=db

    def run(self,limit=24):
        count=0
        for t in self.db.next_tasks(limit):
            self.db.task_state(t["task_id"],"RUNNING",1)
            try:
                result={"task_id":t["task_id"],"title":t["title"],"agent":t.get("agent"),
                        "plugin_id":t.get("plugin_id"),"status":"COMPLETED",
                        "external_side_effects":False,"completed_at":now()}
                self.db.event("task.completed",t.get("agent") or "executor",result)
                self.db.agent_result(t.get("agent") or "planner",True)
                self.db.task_state(t["task_id"],"COMPLETED")
            except Exception as e:
                self.db.event("task.failed","executor",{"task_id":t["task_id"],"error":str(e)})
                self.db.agent_result(t.get("agent") or "planner",False)
                self.db.task_state(t["task_id"],"FAILED")
            count+=1
        return count
