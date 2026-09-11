import json, sqlite3, threading
from pathlib import Path
from contextlib import contextmanager
from .util import now

SCHEMA="""
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS company_builds(
 build_id TEXT PRIMARY KEY,launch_id TEXT,company_id TEXT,company_name TEXT,status TEXT,
 workspace_path TEXT,website_path TEXT,product_path TEXT,marketing_path TEXT,support_path TEXT,
 payload_json TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS connectors(
 connector_id TEXT PRIMARY KEY,name TEXT,category TEXT,status TEXT,mode TEXT,
 config_path TEXT,last_error TEXT,last_checked_at TEXT,payload_json TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS actions(
 action_id TEXT PRIMARY KEY,company_id TEXT,action_type TEXT,status TEXT,risk_level TEXT,
 connector_name TEXT,description TEXT,policy_decision TEXT,attempts INTEGER,
 next_retry_at TEXT,last_error TEXT,payload_json TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS receipts(
 receipt_id TEXT PRIMARY KEY,action_id TEXT,company_id TEXT,connector_name TEXT,
 status TEXT,external_ref TEXT,response_json TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS execution_scores(
 company_id TEXT PRIMARY KEY,successes INTEGER,failures INTEGER,blocked INTEGER,
 execution_score REAL,last_result TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS audit_log(
 id INTEGER PRIMARY KEY AUTOINCREMENT,event_type TEXT,company_id TEXT,actor TEXT,
 decision TEXT,payload_json TEXT,created_at TEXT);
"""

class DB:
    def __init__(self,path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock()
        with self.conn() as c: c.executescript(SCHEMA)
    @contextmanager
    def conn(self):
        c=sqlite3.connect(self.path,timeout=30); c.row_factory=sqlite3.Row
        try:
            yield c; c.commit()
        except Exception:
            c.rollback(); raise
        finally:
            c.close()
    def rows(self,sql,args=()):
        with self.conn() as c:
            return [dict(r) for r in c.execute(sql,args).fetchall()]
    def exec(self,sql,args=()):
        with self.lock,self.conn() as c:
            c.execute(sql,args)
    def audit(self,event_type,company_id,actor,decision,payload):
        self.exec("INSERT INTO audit_log(event_type,company_id,actor,decision,payload_json,created_at) VALUES(?,?,?,?,?,?)",
                  (event_type,company_id,actor,decision,json.dumps(payload,default=str),now()))
