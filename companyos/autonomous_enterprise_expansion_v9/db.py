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
 priority REAL NOT NULL DEFAULT 0,health REAL NOT NULL DEFAULT 100,
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

CREATE TABLE IF NOT EXISTS memories(
 id INTEGER PRIMARY KEY AUTOINCREMENT,memory_type TEXT NOT NULL,subject TEXT NOT NULL,
 company_id TEXT,content_json TEXT NOT NULL,importance REAL NOT NULL DEFAULT 0.5,
 created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS opportunities(
 opportunity_id TEXT PRIMARY KEY,name TEXT NOT NULL,category TEXT,status TEXT NOT NULL,
 score REAL NOT NULL DEFAULT 0,payload_json TEXT NOT NULL,updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS allocation_plans(
 allocation_id TEXT PRIMARY KEY,company_id TEXT,amount_usd REAL NOT NULL,
 priority REAL NOT NULL,status TEXT NOT NULL,payload_json TEXT NOT NULL,updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reassignments(
 reassignment_id TEXT PRIMARY KEY,agent_id TEXT NOT NULL,from_company_id TEXT,to_company_id TEXT,
 reason TEXT NOT NULL,status TEXT NOT NULL,payload_json TEXT NOT NULL,updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS recovery_actions(
 action_id TEXT PRIMARY KEY,company_id TEXT,action_type TEXT NOT NULL,status TEXT NOT NULL,
 priority INTEGER NOT NULL,payload_json TEXT NOT NULL,updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events(
 id INTEGER PRIMARY KEY AUTOINCREMENT,event_type TEXT NOT NULL,source TEXT,target TEXT,
 payload_json TEXT NOT NULL,created_at TEXT NOT NULL
);
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

    def set_kv(self,k,v):
        with self.lock,self.conn() as c:
            c.execute("""INSERT INTO kv VALUES(?,?,?)
            ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json,updated_at=excluded.updated_at""",
            (k,json.dumps(v,default=str),now()))

    def get_kv(self,k,d=None):
        with self.conn() as c:
            r=c.execute("SELECT value_json FROM kv WHERE key=?",(k,)).fetchone()
            return json.loads(r["value_json"]) if r else d

    def event(self,t,source,payload,target=None):
        with self.lock,self.conn() as c:
            c.execute("INSERT INTO events(event_type,source,target,payload_json,created_at) VALUES(?,?,?,?,?)",
                      (t,source,target,json.dumps(payload,default=str),now()))

    def list_events(self,n=500):
        rs=self.rows("SELECT * FROM events ORDER BY id DESC LIMIT ?",(n,))
        for r in rs: r["payload"]=json.loads(r["payload_json"])
        return rs

    def upsert_company(self,cid,name,status,priority,health,payload):
        with self.lock,self.conn() as c:
            c.execute("""INSERT INTO companies VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(company_id) DO UPDATE SET name=excluded.name,status=excluded.status,
            priority=excluded.priority,health=excluded.health,payload_json=excluded.payload_json,
            updated_at=excluded.updated_at""",
            (cid,name,status,float(priority or 0),float(health or 0),json.dumps(payload,default=str),now()))

    def list_companies(self):
        rs=self.rows("SELECT * FROM companies ORDER BY priority DESC,name")
        for r in rs:r["payload"]=json.loads(r["payload_json"])
        return rs

    def upsert_agent(self,aid,cid,name,role,enabled,completed,failed,score,payload):
        with self.lock,self.conn() as c:
            c.execute("""INSERT INTO agents VALUES(?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(agent_id) DO UPDATE SET company_id=excluded.company_id,name=excluded.name,
            role=excluded.role,enabled=excluded.enabled,completed=excluded.completed,failed=excluded.failed,
            score=excluded.score,payload_json=excluded.payload_json,updated_at=excluded.updated_at""",
            (aid,cid,name,role,1 if enabled else 0,int(completed or 0),int(failed or 0),
             float(score or 0),json.dumps(payload,default=str),now()))

    def list_agents(self):
        rs=self.rows("SELECT * FROM agents ORDER BY score DESC,name")
        for r in rs:r["payload"]=json.loads(r["payload_json"])
        return rs

    def add_task(self,tid,cid,kind,title,priority,aid,payload):
        ts=now()
        with self.lock,self.conn() as c:
            c.execute("""INSERT OR IGNORE INTO tasks(task_id,company_id,kind,title,status,priority,agent_id,payload_json,attempts,created_at,updated_at)
            VALUES(?,?,?,?,'QUEUED',?,?,?,0,?,?)""",
            (tid,cid,kind,title,int(priority),aid,json.dumps(payload,default=str),ts,ts))

    def next_tasks(self,n=80):
        rs=self.rows("SELECT * FROM tasks WHERE status='QUEUED' ORDER BY priority DESC,created_at LIMIT ?",(n,))
        for r in rs:r["payload"]=json.loads(r["payload_json"])
        return rs

    def task_state(self,tid,status,attempts_delta=0):
        with self.lock,self.conn() as c:
            c.execute("UPDATE tasks SET status=?,attempts=attempts+?,updated_at=? WHERE task_id=?",
                      (status,int(attempts_delta),now(),tid))

    def list_tasks(self,n=1000):
        rs=self.rows("SELECT * FROM tasks ORDER BY updated_at DESC LIMIT ?",(n,))
        for r in rs:r["payload"]=json.loads(r["payload_json"])
        return rs

    def remember(self,mtype,subject,company_id,content,importance=.5):
        with self.lock,self.conn() as c:
            c.execute("INSERT INTO memories(memory_type,subject,company_id,content_json,importance,created_at) VALUES(?,?,?,?,?,?)",
                      (mtype,subject,company_id,json.dumps(content,default=str),float(importance),now()))

    def list_memories(self,n=500):
        rs=self.rows("SELECT * FROM memories ORDER BY importance DESC,id DESC LIMIT ?",(n,))
        for r in rs:r["content"]=json.loads(r["content_json"])
        return rs

    def upsert_opportunity(self,oid,name,category,status,score,payload):
        with self.lock,self.conn() as c:
            c.execute("""INSERT INTO opportunities VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(opportunity_id) DO UPDATE SET name=excluded.name,category=excluded.category,
            status=excluded.status,score=excluded.score,payload_json=excluded.payload_json,
            updated_at=excluded.updated_at""",
            (oid,name,category,status,float(score or 0),json.dumps(payload,default=str),now()))

    def list_opportunities(self):
        rs=self.rows("SELECT * FROM opportunities ORDER BY score DESC,name")
        for r in rs:r["payload"]=json.loads(r["payload_json"])
        return rs

    def upsert_allocation(self,aid,cid,amount,priority,status,payload):
        with self.lock,self.conn() as c:
            c.execute("""INSERT INTO allocation_plans VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(allocation_id) DO UPDATE SET amount_usd=excluded.amount_usd,
            priority=excluded.priority,status=excluded.status,payload_json=excluded.payload_json,
            updated_at=excluded.updated_at""",
            (aid,cid,float(amount),float(priority),status,json.dumps(payload,default=str),now()))

    def list_allocations(self):
        rs=self.rows("SELECT * FROM allocation_plans ORDER BY priority DESC")
        for r in rs:r["payload"]=json.loads(r["payload_json"])
        return rs

    def upsert_reassignment(self,rid,agent_id,from_c,to_c,reason,status,payload):
        with self.lock,self.conn() as c:
            c.execute("""INSERT INTO reassignments VALUES(?,?,?,?,?,?,?,?)
            ON CONFLICT(reassignment_id) DO UPDATE SET from_company_id=excluded.from_company_id,
            to_company_id=excluded.to_company_id,reason=excluded.reason,status=excluded.status,
            payload_json=excluded.payload_json,updated_at=excluded.updated_at""",
            (rid,agent_id,from_c,to_c,reason,status,json.dumps(payload,default=str),now()))

    def list_reassignments(self):
        rs=self.rows("SELECT * FROM reassignments ORDER BY updated_at DESC")
        for r in rs:r["payload"]=json.loads(r["payload_json"])
        return rs

    def upsert_recovery(self,aid,cid,atype,status,priority,payload):
        with self.lock,self.conn() as c:
            c.execute("""INSERT INTO recovery_actions VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(action_id) DO UPDATE SET status=excluded.status,priority=excluded.priority,
            payload_json=excluded.payload_json,updated_at=excluded.updated_at""",
            (aid,cid,atype,status,int(priority),json.dumps(payload,default=str),now()))

    def list_recovery(self):
        rs=self.rows("SELECT * FROM recovery_actions ORDER BY priority DESC,updated_at DESC")
        for r in rs:r["payload"]=json.loads(r["payload_json"])
        return rs
