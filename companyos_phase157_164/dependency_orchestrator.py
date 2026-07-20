class DependencyOrchestrator:
    """158: release tasks automatically when dependencies complete."""
    def ready(self,tasks,completed):
        done=set(completed); out=[]
        for t in tasks:
            if t.get("status","queued")=="queued" and set(t.get("depends_on",[])).issubset(done):
                out.append({**t,"ready":True})
        return out
