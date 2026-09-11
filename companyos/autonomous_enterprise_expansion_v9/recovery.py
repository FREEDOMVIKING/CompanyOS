from .util import stable_id

class RecoveryEngine:
    def __init__(self,db):
        self.db=db

    def analyze(self):
        count=0
        for c in self.db.list_companies():
            h=float(c.get("health",100) or 100)
            if h<90:
                aid=stable_id("recovery",c["company_id"],"health")
                self.db.upsert_recovery(aid,c["company_id"],"HEALTH_RECOVERY","PROPOSED_INTERNAL_ONLY",95,{
                    "company_name":c["name"],
                    "health":h,
                    "recommended_actions":[
                        "Review failed tasks",
                        "Reduce low-value workload",
                        "Reassign high-performing internal agents",
                        "Re-run validation before expansion"
                    ],
                    "external_side_effects":False
                })
                count+=1
        return count
