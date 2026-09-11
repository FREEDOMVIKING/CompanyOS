class CrossDepartmentCoordinator:
    def coordinate(self, department_updates):
        updates=list(department_updates or [])
        blockers=[]
        handoffs=[]
        for u in updates:
            for b in u.get("blockers",[]):
                blockers.append({"department":u.get("department"),"blocker":b})
            for h in u.get("handoffs",[]):
                handoffs.append({"from":u.get("department"),**h})
        return {"blockers":blockers,"handoffs":handoffs,"departments_seen":len(updates)}
