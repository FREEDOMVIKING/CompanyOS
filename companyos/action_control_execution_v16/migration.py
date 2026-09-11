import sqlite3
from pathlib import Path
from .util import now

class V15Migrator:
    def __init__(self,home,db):
        self.home=Path(home); self.db=db
        self.src=self.home/".companyos_enterprise_v15/companyos_enterprise_v15.sqlite3"

    def run(self):
        counts={"company_builds":0,"connectors":0,"actions":0}
        if not self.src.exists():
            return {"status":"no_v15_database","counts":counts,"updated_at":now()}
        c=sqlite3.connect(self.src); c.row_factory=sqlite3.Row
        try:
            try:
                for r in c.execute("SELECT * FROM company_builds"):
                    d=dict(r)
                    self.db.exec("INSERT OR REPLACE INTO company_builds VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                        (d["build_id"],d["launch_id"],d["company_id"],d["company_name"],d["status"],
                         d["workspace_path"],d["website_path"],d["product_path"],d["marketing_path"],
                         d["support_path"],d.get("payload_json") or "{}",now()))
                    counts["company_builds"]+=1
            except Exception: pass

            try:
                for r in c.execute("SELECT * FROM connectors"):
                    d=dict(r)
                    self.db.exec("INSERT OR REPLACE INTO connectors VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (d["connector_id"],d["name"],d["category"],d["status"],d["mode"],
                         d["config_path"],d.get("last_error"),d.get("last_checked_at"),
                         d.get("payload_json") or "{}",now()))
                    counts["connectors"]+=1
            except Exception: pass

            try:
                for r in c.execute("SELECT * FROM action_queue"):
                    d=dict(r)
                    self.db.exec("INSERT OR REPLACE INTO actions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (d["action_id"],d["company_id"],d["action_type"],d.get("status","REVIEW_REQUIRED"),
                         d.get("risk_level","MEDIUM"),d.get("connector_name",""),d.get("description",""),
                         "UNREVIEWED",0,None,None,d.get("payload_json") or "{}",now()))
                    counts["actions"]+=1
            except Exception: pass
        finally:
            c.close()
        return {"status":"migration_complete","counts":counts,"updated_at":now()}
