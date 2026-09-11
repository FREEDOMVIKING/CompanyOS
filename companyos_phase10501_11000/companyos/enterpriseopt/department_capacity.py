class DepartmentCapacityPlanner:
    def plan(self, departments):
        out=[]
        for d in departments or []:
            demand=float(d.get("demand",0))
            capacity=max(.01,float(d.get("capacity",0)))
            utilization=demand/capacity
            action="normal"
            if utilization>1.2: action="add_capacity"
            elif utilization<.5: action="redeploy_capacity"
            out.append({**d,"utilization":round(utilization,3),"action":action})
        return out
