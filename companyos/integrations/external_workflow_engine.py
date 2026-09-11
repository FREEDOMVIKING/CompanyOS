class ExternalWorkflowEngine:
    def build(self, objective, steps):
        return {
            "objective":objective,
            "steps":[{**s,"status":"pending"} for s in (steps or [])],
            "status":"planned",
        }

    def advance(self, workflow, completed_step):
        wf=dict(workflow or {})
        steps=[]
        for s in wf.get("steps",[]):
            row=dict(s)
            if row.get("name")==completed_step:
                row["status"]="complete"
            steps.append(row)
        wf["steps"]=steps
        wf["status"]="complete" if steps and all(x.get("status")=="complete" for x in steps) else "running"
        return wf
