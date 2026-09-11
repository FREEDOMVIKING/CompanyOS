class ExecutiveMemory:
    def __init__(self,db):
        self.db=db

    def refresh(self):
        created=0
        existing={(m["memory_type"],m["subject"],m.get("company_id")) for m in self.db.list_memories(1000)}
        for c in self.db.list_companies():
            key=("company_strategy",c["name"],c["company_id"])
            if key in existing:
                continue
            content={
                "priority":c["priority"],
                "health":c["health"],
                "lesson":"Maintain focus on validated demand, product readiness, economics, and repeatable operations."
            }
            self.db.remember("company_strategy",c["name"],c["company_id"],content,.85)
            created+=1
        if ("enterprise_principle","Portfolio Discipline",None) not in existing:
            self.db.remember("enterprise_principle","Portfolio Discipline",None,{
                "lesson":"Prefer evidence-backed growth and preserve rollback paths before major internal changes."
            },.95)
            created+=1
        return created
