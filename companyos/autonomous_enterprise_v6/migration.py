import sqlite3, json
from pathlib import Path
from .util import stable_id, now

class V5Migrator:
    def __init__(self,home,db):
        self.home=Path(home)
        self.db=db
        self.v5=self.home/".companyos_unified_v5/companyos_unified_v5.sqlite3"

    def run(self):
        out={"companies":0,"ventures_seen":0}
        if not self.v5.exists():
            report={"status":"no_v5_database","counts":out,"updated_at":now()}
            self.db.set_kv("migration_report",report)
            return report
        c=sqlite3.connect(self.v5); c.row_factory=sqlite3.Row
        try:
            companies={}
            try:
                for r in c.execute("SELECT * FROM companies"):
                    d=dict(r)
                    cid=d["company_id"]
                    companies[cid]=d
                    self.db.upsert_company(cid,d["name"],d["status"],d.get("payload_json"),0,json.loads(d.get("payload_json") or "{}"))
                    out["companies"]+=1
            except Exception:
                pass

            try:
                for r in c.execute("SELECT * FROM ventures"):
                    d=dict(r)
                    cid=d.get("company_id") or stable_id("company",d["venture_id"],length=16)
                    name=d["name"]
                    priority=float(d.get("score") or 0)
                    self.db.upsert_company(cid,name,"INCUBATING",d["venture_id"],priority,{
                        "venture_stage":d.get("stage"),
                        "source":"v5_migration"
                    })
                    out["ventures_seen"]+=1
            except Exception:
                pass
        finally:
            c.close()
        report={"status":"migration_complete","counts":out,"updated_at":now()}
        self.db.set_kv("migration_report",report)
        self.db.event("migration.complete","v5_migrator",report)
        return report
