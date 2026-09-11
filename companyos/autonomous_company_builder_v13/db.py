import json, sqlite3, threading
from pathlib import Path
from contextlib import contextmanager
from .util import now

SCHEMA="""
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS companies(
 company_id TEXT PRIMARY KEY,name TEXT,status TEXT,priority REAL,health REAL,payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS agents(
 agent_id TEXT PRIMARY KEY,company_id TEXT,name TEXT,role TEXT,score REAL,completed INTEGER,failed INTEGER,payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS venture_handoffs(
 handoff_id TEXT PRIMARY KEY,proposal_id TEXT,status TEXT,company_name TEXT,payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS launch_queue(
 launch_id TEXT PRIMARY KEY,handoff_id TEXT,company_name TEXT,status TEXT,priority INTEGER,
 board_score REAL,recommendation TEXT,payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS company_builds(
 build_id TEXT PRIMARY KEY,launch_id TEXT,company_id TEXT,company_name TEXT,status TEXT,
 workspace_path TEXT,website_path TEXT,product_path TEXT,marketing_path TEXT,support_path TEXT,
 payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS products(
 product_id TEXT PRIMARY KEY,company_id TEXT,name TEXT,product_type TEXT,status TEXT,
 price_hint REAL,payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS campaigns(
 campaign_id TEXT PRIMARY KEY,company_id TEXT,name TEXT,channel TEXT,status TEXT,
 message TEXT,payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS sales_plans(
 sales_id TEXT PRIMARY KEY,company_id TEXT,status TEXT,target_customer TEXT,
 offer TEXT,channel_plan TEXT,payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS support_assets(
 support_id TEXT PRIMARY KEY,company_id TEXT,status TEXT,faq_json TEXT,
 onboarding_text TEXT,payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS revenue_ledger(
 id INTEGER PRIMARY KEY AUTOINCREMENT,company_id TEXT,entry_type TEXT,amount REAL,
 verified INTEGER,description TEXT,created_at TEXT);

CREATE TABLE IF NOT EXISTS lifecycle(
 company_id TEXT PRIMARY KEY,state TEXT,growth_score REAL,health_score REAL,
 next_action TEXT,payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS reinvestment_recommendations(
 recommendation_id TEXT PRIMARY KEY,company_id TEXT,priority INTEGER,allocation_score REAL,
 recommendation TEXT,status TEXT,payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS events(
 id INTEGER PRIMARY KEY AUTOINCREMENT,event_type TEXT,source TEXT,target TEXT,payload_json TEXT,created_at TEXT);
"""

class DB:
    def __init__(self,path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock()
        with self.conn() as c: c.executescript(SCHEMA)

    @contextmanager
    def conn(self):
        c=sqlite3.connect(self.path,timeout=30)
        c.row_factory=sqlite3.Row
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

    def event(self,t,source,payload,target=None):
        self.exec("INSERT INTO events(event_type,source,target,payload_json,created_at) VALUES(?,?,?,?,?)",
                  (t,source,target,json.dumps(payload,default=str),now()))
