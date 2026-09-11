class WorkflowRuntime:
    def start(self, name, steps):
        return {"name":name,"status":"running","steps":[{**s,"status":"pending"} for s in steps or []],"current":0}

    def advance(self, workflow, result=None):
        wf=dict(workflow or {})
        steps=[dict(s) for s in wf.get("steps",[])]
        idx=int(wf.get("current",0))
        if idx < len(steps):
            steps[idx]["status"]="complete"
            steps[idx]["result"]=result or {}
            idx+=1
        wf["steps"]=steps
        wf["current"]=idx
        wf["status"]="complete" if idx>=len(steps) else "running"
        return wf
