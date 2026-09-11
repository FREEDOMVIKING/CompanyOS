from pathlib import Path
from .util import read_json, stable_id

class OpportunityEngine:
    def __init__(self,home,db):
        self.home=Path(home)
        self.db=db
        self.inbox=self.home/".companyos_enterprise_v9/opportunities_inbox.json"
        self.inbox.parent.mkdir(parents=True,exist_ok=True)

    def ingest(self):
        data=read_json(self.inbox,{"opportunities":[]})
        count=0
        for o in data.get("opportunities",[]) or []:
            name=o.get("name")
            if not name: continue
            vals=[float(o.get(k,0) or 0) for k in ("demand_score","margin_score","execution_score","strategic_fit")]
            score=round(sum(vals)/4,2)
            oid=o.get("opportunity_id") or stable_id("opportunity",name,o.get("category"))
            status="HIGH_PRIORITY" if score>=85 else "VALIDATE_MORE" if score>=70 else "LOW_PRIORITY"
            self.db.upsert_opportunity(oid,name,o.get("category") or "unknown",status,score,o)
            count+=1
        return count
