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

CREATE TABLE IF NOT EXISTS research_sources(
 source_id TEXT PRIMARY KEY,name TEXT,source_type TEXT,url TEXT,enabled INTEGER,status TEXT,
 last_http_status INTEGER,last_error TEXT,last_checked_at TEXT,payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS research_items(
 item_id TEXT PRIMARY KEY,source_id TEXT,title TEXT,url TEXT,published_at TEXT,summary TEXT,
 category TEXT,payload_json TEXT,created_at TEXT);

CREATE TABLE IF NOT EXISTS opportunity_candidates(
 opportunity_id TEXT PRIMARY KEY,name TEXT,category TEXT,status TEXT,
 demand_score REAL,margin_score REAL,execution_score REAL,strategic_fit REAL,
 evidence_score REAL,total_score REAL,evidence_count INTEGER,payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS evidence(
 evidence_id TEXT PRIMARY KEY,opportunity_id TEXT,item_id TEXT,evidence_type TEXT,
 weight REAL,payload_json TEXT,created_at TEXT);

CREATE TABLE IF NOT EXISTS validation_queue(
 validation_id TEXT PRIMARY KEY,opportunity_id TEXT,status TEXT,priority INTEGER,
 hypothesis TEXT,payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS venture_proposals(
 proposal_id TEXT PRIMARY KEY,opportunity_id TEXT,name TEXT,status TEXT,score REAL,
 rationale TEXT,payload_json TEXT,updated_at TEXT);

CREATE TABLE IF NOT EXISTS executive_memories(
 id INTEGER PRIMARY KEY AUTOINCREMENT,memory_type TEXT,subject TEXT,company_id TEXT,
 content_json TEXT,importance REAL,created_at TEXT);

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

    def upsert_company(self,d):
        self.exec("""INSERT INTO companies VALUES(?,?,?,?,?,?,?)
        ON CONFLICT(company_id) DO UPDATE SET name=excluded.name,status=excluded.status,
        priority=excluded.priority,health=excluded.health,payload_json=excluded.payload_json,
        updated_at=excluded.updated_at""",
        (d["company_id"],d["name"],d.get("status","MIGRATED"),float(d.get("priority") or 0),
         float(d.get("health") or 100),d.get("payload_json") or "{}",now()))

    def upsert_agent(self,d):
        self.exec("""INSERT INTO agents VALUES(?,?,?,?,?,?,?,?,?)
        ON CONFLICT(agent_id) DO UPDATE SET company_id=excluded.company_id,name=excluded.name,
        role=excluded.role,score=excluded.score,completed=excluded.completed,failed=excluded.failed,
        payload_json=excluded.payload_json,updated_at=excluded.updated_at""",
        (d["agent_id"],d.get("company_id"),d["name"],d.get("role","specialist"),
         float(d.get("score") or 50),int(d.get("completed") or 0),int(d.get("failed") or 0),
         d.get("payload_json") or "{}",now()))
