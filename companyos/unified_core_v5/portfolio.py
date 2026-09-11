from .util import stable_id

class PortfolioEngine:
    def __init__(self,db):
        self.db=db

    def ensure_companies(self):
        for v in self.db.list_ventures():
            cid=v.get("company_id") or stable_id("company",v["venture_id"],length=16)
            self.db.upsert_venture(v["venture_id"],v["name"],v.get("stage"),v.get("score"),v.get("source"),v.get("payload",{}),cid)
            self.db.upsert_company(cid,v["name"],"INCUBATING",{"source_venture_id":v["venture_id"]})
        return len(self.db.list_companies())

    def rank(self):
        rows=[]
        for v in self.db.list_ventures():
            base=float(v.get("score",0) or 0)
            stage=str(v.get("stage") or "").upper()
            bonus=8 if "READY" in stage else 5 if "GROW" in stage else 2 if "VALIDATE" in stage else 0
            rows.append({**v,"executive_priority":round(min(100,base+bonus),2)})
        rows.sort(key=lambda x:x["executive_priority"],reverse=True)
        return rows
