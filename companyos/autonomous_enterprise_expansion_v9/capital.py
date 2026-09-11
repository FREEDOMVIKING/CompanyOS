from .util import stable_id

class CapitalPlanner:
    def __init__(self,db):
        self.db=db

    def plan(self):
        companies=self.db.list_companies()
        if not companies:return 0
        total_weight=sum(max(1,float(c.get("priority",0) or 0)) for c in companies)
        planning_pool=1000.0
        count=0
        for c in companies:
            weight=max(1,float(c.get("priority",0) or 0))
            amount=round(planning_pool*(weight/total_weight),2)
            aid=stable_id("capital",c["company_id"])
            self.db.upsert_allocation(aid,c["company_id"],amount,weight,"PLANNING_ONLY",{
                "automatic_spending":False,
                "planning_pool_usd":planning_pool,
                "health":c.get("health")
            })
            count+=1
        return count
