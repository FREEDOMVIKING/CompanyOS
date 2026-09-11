class DepartmentRouter:
    RULES={
        "research":"research",
        "build":"product",
        "deploy":"operations",
        "email":"sales",
        "customer_support":"customer_success",
        "finance":"finance",
        "growth":"growth",
        "security":"operations",
    }
    def route(self, jobs):
        out=[]
        for j in jobs or []:
            dept=self.RULES.get(j.get("task_type"),j.get("department","operations"))
            out.append({**j,"department":dept})
        return out
