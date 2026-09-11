class DepartmentTaskMarket:
    def assign(self, tasks, departments):
        assignments=[]
        for task in tasks or []:
            best=None; best_score=-1
            for d in departments or []:
                skill=float(d.get("skill_match",{}).get(task.get("type"),0.3))
                capacity=float(d.get("capacity",0.5))
                score=skill*0.7+capacity*0.3
                if score>best_score:
                    best_score=score; best=d
            if best:
                assignments.append({
                    "task":task,
                    "department":best.get("name"),
                    "assignment_score":round(best_score,3)
                })
        return assignments
