import sqlite3
from pathlib import Path
from .util import now

class V10Migrator:
    def __init__(self,home,db):
        self.home=Path(home)
        self.db=db
        self.src=self.home/".companyos_enterprise_v10/companyos_enterprise_v10.sqlite3"

    def run(self):
        counts={"companies":0,"agents":0}
        if not self.src.exists():
            return {"status":"no_v10_database","counts":counts,"updated_at":now()}
        c=sqlite3.connect(self.src); c.row_factory=sqlite3.Row
        try:
            try:
                for r in c.execute("SELECT * FROM companies"):
                    self.db.upsert_company(dict(r)); counts["companies"]+=1
            except Exception:
                pass
            try:
                for r in c.execute("SELECT * FROM agents"):
                    self.db.upsert_agent(dict(r)); counts["agents"]+=1
            except Exception:
                pass
        finally:
            c.close()
        self.db.event("migration.complete","v10_migrator",counts)
        return {"status":"migration_complete","counts":counts,"updated_at":now()}
