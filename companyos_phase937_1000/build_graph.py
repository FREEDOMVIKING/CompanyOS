class BuildDependencyGraph:
    """973-976: task dependency graph for build execution."""
    def build(self, assignments):
        nodes=[]
        deps=[]
        for i,a in enumerate(assignments or []):
            nid=f"task_{i+1}"
            nodes.append({"id":nid,**a})
            if i>0:
                deps.append({"from":f"task_{i}","to":nid})
        return {"nodes":nodes,"dependencies":deps}
