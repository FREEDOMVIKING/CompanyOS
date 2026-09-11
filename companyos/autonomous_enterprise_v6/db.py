import json, sqlite3, threading
from pathlib import Path
from contextlib import contextmanager
from .util import now

SCHEMA="""
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS kv(
 key TEXT PRIMARY KEY,value_json TEXT NOT NULL,updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS companies(
 company_id TEXT PRIMARY KEY,name TEXT NOT NULL,status TEXT NOT NULL,
 venture_id TEXT,priority REAL NOT NULL DEFAULT 0,
 payload_json TEXT NOT NULL,updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS agents(
 agent_id TEXT PRIMARY KEY,company_id TEXT,name TEXT NOT NULL,role TEXT NOT NULL,
 enabled INTEGER NOT NULL DEFAULT 1,completed INTEGER NOT NULL DEFAULT 0,
 failed INTEGER NOT NULL DEFAULT 0,score REAL NOT NULL DEFAULT 50,
 payload_json TEXT NOT NULL,updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks(
 task_id TEXT PRIMARY KEY,company_id TEXT,kind TEXT NOT NULL,title TEXT NOT NULL,
 status TEXT NOT NULL,priority INTEGER NOT NULL DEFAULT 50,agent_id TEXT,
 payload_json TEXT NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,
 created_at TEXT NOT NULL,updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS decisions(
 id INTEGER PRIMARY KEY AUTOINCREMENT,decision_id TEXT UNIQUE NOT NULL,
 company_id TEXT,subject TEXT NOT NULL,decision TEXT NOT NULL,
 rationale TEXT NOT NULL,confidence REAL NOT NULL,
 payload_json TEXT NOT NULL,created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events(
 id INTEGER PRIMARY KEY AUTOINCREMENT,event_type TEXT NOT NULL,
 source TEXT,target TEXT,payload_json TEXT NOT NULL,created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS metrics(
 id INTEGER PRIMARY KEY AUTOINCREMENT,scope_type TEXT NOT NULL,scope_id TEXT NOT NULL,
 metric TEXT NOT NULL,value REAL NOT NULL,metadata_json TEXT NOT NULL,created_at TEXT NOT NULL
);
"""

class DB:
    def __init__(self,path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
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

    def _rows(self,sql,args=()):
        with self.conn() as c:
            return [dict(r) for r in c.execute(sql,args).fetchall()]

    def set_kv(self,k,v):
        with self.lock,self.conn() as c:
            c.execute("""INSERT INTO kv VALUES(?,?,?)
            ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json,updated_at=excluded.updated_at""",
            (k,json.dumps(v,default=str),now()))

    def get_kv(self,k,d=None):
        with self.conn() as c:
            r=c.execute("SELECT value_json FROM kv WHERE key=?",(k,)).fetchone()
            return json.loads(r["value_json"]) if r else d

    def upsert_company(self,cid,name,status,venture_id,priority,payload):
        with self.lock,self.conn() as c:
            c.execute("""INSERT INTO companies VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(company_id) DO UPDATE SET name=excluded.name,status=excluded.status,
            venture_id=excluded.venture_id,priority=excluded.priority,
            payload_json=excluded.payload_json,updated_at=excluded.updated_at""",
            (cid,name,status,venture_id,float(priority or 0),json.dumps(payload,default=str),now()))

    def list_companies(self):
        rs=self._rows("SELECT * FROM companies ORDER BY priority DESC,name")
        for r in rs: r["payload"]=json.loads(r["payload_json"])
        return rs

    def upsert_agent(self,aid,cid,name,role,payload=None,enabled=True):
        with self.lock,self.conn() as c:
            c.execute("""INSERT INTO agents(agent_id,company_id,name,role,enabled,completed,failed,score,payload_json,updated_at)
            VALUES(?,?,?,?,?,0,0,50,?,?)
            ON CONFLICT(agent_id) DO UPDATE SET company_id=excluded.company_id,name=excluded.name,
            role=excluded.role,enabled=excluded.enabled,payload_json=excluded.payload_json,updated_at=excluded.updated_at""",
            (aid,cid,name,role,1 if enabled else 0,json.dumps(payload or {},default=str),now()))

    def list_agents(self):
        rs=self._rows("SELECT * FROM agents ORDER BY score DESC,name")
        for r in rs: r["payload"]=json.loads(r["payload_json"])
        return rs

    def agent_result(self,aid,ok):
        with self.lock,self.conn() as c:
            r=c.execute("SELECT completed,failed FROM agents WHERE agent_id=?",(aid,)).fetchone()
            if not r: return
            comp=r["completed"]+(1 if ok else 0)
            fail=r["failed"]+(0 if ok else 1)
            score=round(100*comp/max(1,comp+fail),2)
            c.execute("UPDATE agents SET completed=?,failed=?,score=?,updated_at=? WHERE agent_id=?",
                      (comp,fail,score,now(),aid))

    def add_task(self,tid,cid,kind,title,priority,aid,payload):
        ts=now()
        with self.lock,self.conn() as c:
            c.execute("""INSERT OR IGNORE INTO tasks(task_id,company_id,kind,title,status,priority,agent_id,payload_json,attempts,created_at,updated_at)
            VALUES(?,?,?,?,'QUEUED',?,?,?,0,?,?)""",
            (tid,cid,kind,title,int(priority),aid,json.dumps(payload,default=str),ts,ts))

    def next_tasks(self,n=30):
        rs=self._rows("SELECT * FROM tasks WHERE status='QUEUED' ORDER BY priority DESC,created_at LIMIT ?",(n,))
        for r in rs: r["payload"]=json.loads(r["payload_json"])
        return rs

    def task_state(self,tid,status,attempts_delta=0):
        with self.lock,self.conn() as c:
            c.execute("UPDATE tasks SET status=?,attempts=attempts+?,updated_at=? WHERE task_id=?",
                      (status,int(attempts_delta),now(),tid))

    def list_tasks(self,n=500):
        rs=self._rows("SELECT * FROM tasks ORDER BY updated_at DESC LIMIT ?",(n,))
        for r in rs: r["payload"]=json.loads(r["payload_json"])
        return rs

    def record_decision(self,did,cid,subject,decision,rationale,confidence,payload):
        with self.lock,self.conn() as c:
            c.execute("""INSERT OR IGNORE INTO decisions(decision_id,company_id,subject,decision,rationale,confidence,payload_json,created_at)
            VALUES(?,?,?,?,?,?,?,?)""",
            (did,cid,subject,decision,rationale,float(confidence),json.dumps(payload,default=str),now()))

    def list_decisions(self,n=200):
        rs=self._rows("SELECT * FROM decisions ORDER BY id DESC LIMIT ?",(n,))
        for r in rs: r["payload"]=json.loads(r["payload_json"])
        return rs

    def event(self,t,source,payload,target=None):
        with self.lock,self.conn() as c:
            c.execute("INSERT INTO events(event_type,source,target,payload_json,created_at) VALUES(?,?,?,?,?)",
                      (t,source,target,json.dumps(payload,default=str),now()))

    def list_events(self,n=300):
        rs=self._rows("SELECT * FROM events ORDER BY id DESC LIMIT ?",(n,))
        for r in rs: r["payload"]=json.loads(r["payload_json"])
        return rs

    def metric(self,scope_type,scope_id,metric,value,metadata=None):
        with self.lock,self.conn() as c:
            c.execute("INSERT INTO metrics(scope_type,scope_id,metric,value,metadata_json,created_at) VALUES(?,?,?,?,?,?)",
                      (scope_type,scope_id,metric,float(value),json.dumps(metadata or {},default=str),now()))

    def recent_metrics(self,n=300):
        rs=self._rows("SELECT * FROM metrics ORDER BY id DESC LIMIT ?",(n,))
        for r in rs: r["metadata"]=json.loads(r["metadata_json"])
        return rs
