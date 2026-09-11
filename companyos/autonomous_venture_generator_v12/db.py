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

CREATE TABLE IF NOT EXISTS opportunities(
 opportunity_id TEXT PRIMARY KEY,name TEXT,category TEXT,status TEXT,total_score REAL,
 evidence_count INTEGER,payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS venture_proposals(
 proposal_id TEXT PRIMARY KEY,opportunity_id TEXT,name TEXT,category TEXT,status TEXT,
 opportunity_score REAL,venture_score REAL,business_model TEXT,revenue_model TEXT,
 startup_cost_low REAL,startup_cost_high REAL,risk_level TEXT,rationale TEXT,payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS business_plans(
 plan_id TEXT PRIMARY KEY,proposal_id TEXT,problem TEXT,customer TEXT,offer TEXT,
 differentiation TEXT,go_to_market TEXT,operations TEXT,kpis_json TEXT,payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS milestones(
 milestone_id TEXT PRIMARY KEY,proposal_id TEXT,sequence_no INTEGER,title TEXT,
 success_criteria TEXT,status TEXT,payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS launch_packages(
 launch_id TEXT PRIMARY KEY,proposal_id TEXT,status TEXT,launch_score REAL,
 checklist_json TEXT,assets_json TEXT,payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS executive_review(
 review_id TEXT PRIMARY KEY,proposal_id TEXT,status TEXT,priority INTEGER,
 recommendation TEXT,payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS company_handoffs(
 handoff_id TEXT PRIMARY KEY,proposal_id TEXT,status TEXT,company_name TEXT,
 payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS events(
 id INTEGER PRIMARY KEY AUTOINCREMENT,event_type TEXT,source TEXT,target TEXT,payload_json TEXT,created_at TEXT);
"""

class DB:
    def __init__(self,path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock()
        with self.conn() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def conn(self):
        c=sqlite3.connect(self.path,timeout=30)
        c.row_factory=sqlite3.Row
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise
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
