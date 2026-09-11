import sqlite3
from pathlib import Path
from .util import now

class V12Migrator:
    def __init__(self,home,db):
        self.home=Path(home)
        self.db=db
        self.src=self.home/".companyos_enterprise_v12/companyos_enterprise_v12.sqlite3"

    def run(self):
        counts={"companies":0,"agents":0,"handoffs":0}
        if not self.src.exists():
            return {"status":"no_v12_database","counts":counts,"updated_at":now()}
        c=sqlite3.connect(self.src); c.row_factory=sqlite3.Row
        try:
            try:
                for r in c.execute("SELECT * FROM companies"):
                    d=dict(r)
                    self.db.exec("INSERT OR REPLACE INTO companies VALUES(?,?,?,?,?,?,?)",
                                 (d["company_id"],d["name"],d.get("status","MIGRATED"),
                                  float(d.get("priority") or 0),float(d.get("health") or 100),
                                  d.get("payload_json") or "{}",now()))
                    counts["companies"]+=1
            except Exception: pass
            try:
                for r in c.execute("SELECT * FROM agents"):
                    d=dict(r)
                    self.db.exec("INSERT OR REPLACE INTO agents VALUES(?,?,?,?,?,?,?,?,?)",
                                 (d["agent_id"],d.get("company_id"),d["name"],d.get("role","specialist"),
                                  float(d.get("score") or 50),int(d.get("completed") or 0),int(d.get("failed") or 0),
                                  d.get("payload_json") or "{}",now()))
                    counts["agents"]+=1
            except Exception: pass
            try:
                for r in c.execute("SELECT * FROM company_handoffs"):
                    d=dict(r)
                    self.db.exec("INSERT OR REPLACE INTO venture_handoffs VALUES(?,?,?,?,?,?)",
                                 (d["handoff_id"],d["proposal_id"],d["status"],d["company_name"],
                                  d.get("payload_json") or "{}",now()))
                    counts["handoffs"]+=1
            except Exception: pass
        finally:
            c.close()
        self.db.event("migration.complete","v12_migrator",counts)
        return {"status":"migration_complete","counts":counts,"updated_at":now()}
