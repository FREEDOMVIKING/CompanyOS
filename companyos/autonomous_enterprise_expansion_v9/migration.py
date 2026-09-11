import sqlite3, json
from pathlib import Path
from .util import now

class V8Migrator:
    def __init__(self,home,db):
        self.home=Path(home)
        self.db=db
        self.v8=self.home/".companyos_enterprise_v8/companyos_enterprise_v8.sqlite3"

    def run(self):
        counts={"companies":0,"agents":0}
        if not self.v8.exists():
            report={"status":"no_v8_database","counts":counts,"updated_at":now()}
            self.db.set_kv("migration_report",report)
            return report
        c=sqlite3.connect(self.v8)
        c.row_factory=sqlite3.Row
        try:
            for r in c.execute("SELECT * FROM companies"):
                d=dict(r)
                self.db.upsert_company(d["company_id"],d["name"],d["status"],
                                       d.get("priority",0),d.get("health",100),
                                       json.loads(d.get("payload") or "{}"))
                counts["companies"]+=1
            for r in c.execute("SELECT * FROM agents"):
                d=dict(r)
                self.db.upsert_agent(d["agent_id"],d.get("company_id"),d["name"],d["role"],True,
                                     d.get("completed",0),d.get("failed",0),d.get("score",50),
                                     json.loads(d.get("payload") or "{}"))
                counts["agents"]+=1
        finally:
            c.close()
        report={"status":"migration_complete","counts":counts,"updated_at":now()}
        self.db.set_kv("migration_report",report)
        self.db.event("migration.complete","v8_migrator",report)
        return report
