import json, sqlite3, threading
from pathlib import Path
from contextlib import contextmanager
from .util import now

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS kv(
 key TEXT PRIMARY KEY,
 value_json TEXT NOT NULL,
 updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS modules(
 module_id TEXT PRIMARY KEY,
 name TEXT NOT NULL,
 source TEXT,
 status TEXT,
 healthy INTEGER NOT NULL DEFAULT 0,
 payload_json TEXT NOT NULL,
 updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ventures(
 venture_id TEXT PRIMARY KEY,
 company_id TEXT,
 name TEXT NOT NULL,
 stage TEXT,
 score REAL NOT NULL DEFAULT 0,
 source TEXT,
 payload_json TEXT NOT NULL,
 updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS companies(
 company_id TEXT PRIMARY KEY,
 name TEXT NOT NULL,
 status TEXT NOT NULL,
 venture_count INTEGER NOT NULL DEFAULT 0,
 revenue_usd REAL NOT NULL DEFAULT 0,
 cost_usd REAL NOT NULL DEFAULT 0,
 payload_json TEXT NOT NULL,
 updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agents(
 agent_id TEXT PRIMARY KEY,
 name TEXT NOT NULL,
 role TEXT NOT NULL,
 enabled INTEGER NOT NULL DEFAULT 1,
 completed INTEGER NOT NULL DEFAULT 0,
 failed INTEGER NOT NULL DEFAULT 0,
 score REAL NOT NULL DEFAULT 50,
 updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks(
 task_id TEXT PRIMARY KEY,
 kind TEXT NOT NULL,
 title TEXT NOT NULL,
 status TEXT NOT NULL,
 priority INTEGER NOT NULL DEFAULT 50,
 agent TEXT,
 plugin_id TEXT,
 payload_json TEXT NOT NULL,
 attempts INTEGER NOT NULL DEFAULT 0,
 max_attempts INTEGER NOT NULL DEFAULT 3,
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 event_type TEXT NOT NULL,
 source TEXT,
 target TEXT,
 payload_json TEXT NOT NULL,
 created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS goals(
 goal_id TEXT PRIMARY KEY,
 title TEXT NOT NULL,
 venture_id TEXT,
 company_id TEXT,
 status TEXT NOT NULL,
 priority INTEGER NOT NULL DEFAULT 50,
 parent_goal_id TEXT,
 dependencies_json TEXT NOT NULL,
 payload_json TEXT NOT NULL,
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memories(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 memory_type TEXT NOT NULL,
 subject TEXT NOT NULL,
 content_json TEXT NOT NULL,
 importance REAL NOT NULL DEFAULT 0.5,
 created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decisions(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 decision_id TEXT UNIQUE NOT NULL,
 subject TEXT NOT NULL,
 decision TEXT NOT NULL,
 rationale TEXT NOT NULL,
 confidence REAL NOT NULL,
 payload_json TEXT NOT NULL,
 created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plugins(
 plugin_id TEXT PRIMARY KEY,
 name TEXT NOT NULL,
 version TEXT NOT NULL,
 enabled INTEGER NOT NULL DEFAULT 1,
 source TEXT,
 entrypoint TEXT,
 capabilities_json TEXT NOT NULL,
 health TEXT NOT NULL DEFAULT 'UNKNOWN',
 updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS metrics(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 scope_type TEXT NOT NULL,
 scope_id TEXT NOT NULL,
 metric TEXT NOT NULL,
 value REAL NOT NULL,
 metadata_json TEXT NOT NULL,
 created_at TEXT NOT NULL
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

    def event(self,t,source,payload,target=None):
        with self.lock,self.conn() as c:
            c.execute("INSERT INTO events(event_type,source,target,payload_json,created_at) VALUES(?,?,?,?,?)",
                      (t,source,target,json.dumps(payload,default=str),now()))

    def list_events(self,n=250):
        rs=self._rows("SELECT * FROM events ORDER BY id DESC LIMIT ?",(n,))
        for r in rs: r["payload"]=json.loads(r["payload_json"])
        return rs

    def upsert_module(self,mid,name,source,status,healthy,payload):
        with self.lock,self.conn() as c:
            c.execute("""INSERT INTO modules VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(module_id) DO UPDATE SET name=excluded.name,source=excluded.source,status=excluded.status,
            healthy=excluded.healthy,payload_json=excluded.payload_json,updated_at=excluded.updated_at""",
            (mid,name,source,status,1 if healthy else 0,json.dumps(payload,default=str),now()))

    def list_modules(self):
        rs=self._rows("SELECT * FROM modules ORDER BY healthy DESC,name")
        for r in rs: r["payload"]=json.loads(r["payload_json"])
        return rs

    def upsert_venture(self,vid,name,stage,score,source,payload,company_id=None):
        with self.lock,self.conn() as c:
            c.execute("""INSERT INTO ventures VALUES(?,?,?,?,?,?,?,?)
            ON CONFLICT(venture_id) DO UPDATE SET company_id=excluded.company_id,name=excluded.name,
            stage=excluded.stage,score=excluded.score,source=excluded.source,payload_json=excluded.payload_json,
            updated_at=excluded.updated_at""",
            (vid,company_id,name,stage,float(score or 0),source,json.dumps(payload,default=str),now()))

    def list_ventures(self):
        rs=self._rows("SELECT * FROM ventures ORDER BY score DESC,name")
        for r in rs: r["payload"]=json.loads(r["payload_json"])
        return rs

    def upsert_company(self,cid,name,status,payload):
        with self.lock,self.conn() as c:
            ventures=c.execute("SELECT COUNT(*) n FROM ventures WHERE company_id=?",(cid,)).fetchone()["n"]
            c.execute("""INSERT INTO companies(company_id,name,status,venture_count,revenue_usd,cost_usd,payload_json,updated_at)
            VALUES(?,?,?,?,0,0,?,?)
            ON CONFLICT(company_id) DO UPDATE SET name=excluded.name,status=excluded.status,
            venture_count=excluded.venture_count,payload_json=excluded.payload_json,updated_at=excluded.updated_at""",
            (cid,name,status,ventures,json.dumps(payload,default=str),now()))

    def list_companies(self):
        rs=self._rows("SELECT * FROM companies ORDER BY revenue_usd DESC,name")
        for r in rs: r["payload"]=json.loads(r["payload_json"])
        return rs

    def upsert_agent(self,aid,name,role,enabled=True):
        with self.lock,self.conn() as c:
            c.execute("""INSERT INTO agents(agent_id,name,role,enabled,completed,failed,score,updated_at)
            VALUES(?,?,?,?,0,0,50,?)
            ON CONFLICT(agent_id) DO UPDATE SET name=excluded.name,role=excluded.role,enabled=excluded.enabled,updated_at=excluded.updated_at""",
            (aid,name,role,1 if enabled else 0,now()))

    def agent_result(self,aid,ok):
        with self.lock,self.conn() as c:
            row=c.execute("SELECT completed,failed FROM agents WHERE agent_id=?",(aid,)).fetchone()
            if not row: return
            comp=row["completed"]+(1 if ok else 0)
            fail=row["failed"]+(0 if ok else 1)
            total=max(1,comp+fail)
            score=round(100*comp/total,2)
            c.execute("UPDATE agents SET completed=?,failed=?,score=?,updated_at=? WHERE agent_id=?",
                      (comp,fail,score,now(),aid))

    def list_agents(self):
        return self._rows("SELECT * FROM agents ORDER BY score DESC,name")

    def add_task(self,tid,kind,title,priority,agent,payload,plugin_id=None,max_attempts=3):
        ts=now()
        with self.lock,self.conn() as c:
            c.execute("""INSERT OR IGNORE INTO tasks(task_id,kind,title,status,priority,agent,plugin_id,payload_json,attempts,max_attempts,created_at,updated_at)
            VALUES(?,?,?,'QUEUED',?,?,?,?,0,?,?,?)""",
            (tid,kind,title,int(priority),agent,plugin_id,json.dumps(payload,default=str),int(max_attempts),ts,ts))

    def next_tasks(self,n=20):
        rs=self._rows("SELECT * FROM tasks WHERE status='QUEUED' ORDER BY priority DESC,created_at LIMIT ?",(n,))
        for r in rs: r["payload"]=json.loads(r["payload_json"])
        return rs

    def task_state(self,tid,status,attempts_delta=0):
        with self.lock,self.conn() as c:
            c.execute("UPDATE tasks SET status=?,attempts=attempts+?,updated_at=? WHERE task_id=?",
                      (status,int(attempts_delta),now(),tid))

    def list_tasks(self,n=400):
        rs=self._rows("SELECT * FROM tasks ORDER BY updated_at DESC LIMIT ?",(n,))
        for r in rs: r["payload"]=json.loads(r["payload_json"])
        return rs

    def upsert_goal(self,gid,title,venture_id,company_id,status,priority,parent_goal_id,deps,payload):
        ts=now()
        with self.lock,self.conn() as c:
            c.execute("""INSERT INTO goals VALUES(?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(goal_id) DO UPDATE SET title=excluded.title,status=excluded.status,
            priority=excluded.priority,dependencies_json=excluded.dependencies_json,
            payload_json=excluded.payload_json,updated_at=excluded.updated_at""",
            (gid,title,venture_id,company_id,status,int(priority),parent_goal_id,
             json.dumps(deps),json.dumps(payload,default=str),ts,ts))

    def list_goals(self):
        rs=self._rows("SELECT * FROM goals ORDER BY priority DESC,created_at")
        for r in rs:
            r["dependencies"]=json.loads(r["dependencies_json"])
            r["payload"]=json.loads(r["payload_json"])
        return rs

    def remember(self,mtype,subject,content,importance=.5):
        with self.lock,self.conn() as c:
            c.execute("INSERT INTO memories(memory_type,subject,content_json,importance,created_at) VALUES(?,?,?,?,?)",
                      (mtype,subject,json.dumps(content,default=str),float(importance),now()))

    def list_memories(self,n=150):
        rs=self._rows("SELECT * FROM memories ORDER BY importance DESC,id DESC LIMIT ?",(n,))
        for r in rs: r["content"]=json.loads(r["content_json"])
        return rs

    def record_decision(self,did,subject,decision,rationale,confidence,payload):
        with self.lock,self.conn() as c:
            c.execute("""INSERT OR IGNORE INTO decisions(decision_id,subject,decision,rationale,confidence,payload_json,created_at)
            VALUES(?,?,?,?,?,?,?)""",
            (did,subject,decision,rationale,float(confidence),json.dumps(payload,default=str),now()))

    def list_decisions(self,n=150):
        rs=self._rows("SELECT * FROM decisions ORDER BY id DESC LIMIT ?",(n,))
        for r in rs: r["payload"]=json.loads(r["payload_json"])
        return rs

    def upsert_plugin(self,pid,name,version,source,entrypoint,caps,enabled=True,health="OK"):
        with self.lock,self.conn() as c:
            c.execute("""INSERT INTO plugins VALUES(?,?,?,?,?,?,?,?,?)
            ON CONFLICT(plugin_id) DO UPDATE SET name=excluded.name,version=excluded.version,
            enabled=excluded.enabled,source=excluded.source,entrypoint=excluded.entrypoint,
            capabilities_json=excluded.capabilities_json,health=excluded.health,updated_at=excluded.updated_at""",
            (pid,name,version,1 if enabled else 0,source,entrypoint,json.dumps(caps,default=str),health,now()))

    def list_plugins(self):
        rs=self._rows("SELECT * FROM plugins ORDER BY name")
        for r in rs: r["capabilities"]=json.loads(r["capabilities_json"])
        return rs

    def metric(self,scope_type,scope_id,metric,value,metadata=None):
        with self.lock,self.conn() as c:
            c.execute("INSERT INTO metrics(scope_type,scope_id,metric,value,metadata_json,created_at) VALUES(?,?,?,?,?,?)",
                      (scope_type,scope_id,metric,float(value),json.dumps(metadata or {},default=str),now()))

    def recent_metrics(self,n=250):
        rs=self._rows("SELECT * FROM metrics ORDER BY id DESC LIMIT ?",(n,))
        for r in rs: r["metadata"]=json.loads(r["metadata_json"])
        return rs
