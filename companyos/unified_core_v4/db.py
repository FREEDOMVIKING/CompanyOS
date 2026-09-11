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

CREATE TABLE IF NOT EXISTS modules(
 module_id TEXT PRIMARY KEY,name TEXT NOT NULL,source TEXT,status TEXT,
 healthy INTEGER NOT NULL DEFAULT 0,payload_json TEXT NOT NULL,updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ventures(
 venture_id TEXT PRIMARY KEY,name TEXT NOT NULL,stage TEXT,score REAL NOT NULL DEFAULT 0,
 source TEXT,payload_json TEXT NOT NULL,updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agents(
 agent_id TEXT PRIMARY KEY,name TEXT NOT NULL,role TEXT NOT NULL,
 enabled INTEGER NOT NULL DEFAULT 1,completed INTEGER NOT NULL DEFAULT 0,
 failed INTEGER NOT NULL DEFAULT 0,updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks(
 task_id TEXT PRIMARY KEY,kind TEXT NOT NULL,title TEXT NOT NULL,status TEXT NOT NULL,
 priority INTEGER NOT NULL DEFAULT 50,agent TEXT,payload_json TEXT NOT NULL,
 attempts INTEGER NOT NULL DEFAULT 0,max_attempts INTEGER NOT NULL DEFAULT 3,
 created_at TEXT NOT NULL,updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events(
 id INTEGER PRIMARY KEY AUTOINCREMENT,event_type TEXT NOT NULL,source TEXT,target TEXT,
 payload_json TEXT NOT NULL,created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plugins(
 plugin_id TEXT PRIMARY KEY,name TEXT NOT NULL,version TEXT NOT NULL,
 enabled INTEGER NOT NULL DEFAULT 1,source TEXT,capabilities_json TEXT NOT NULL,
 health TEXT NOT NULL DEFAULT 'OK',updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS goals(
 goal_id TEXT PRIMARY KEY,title TEXT NOT NULL,venture_id TEXT,status TEXT NOT NULL,
 priority INTEGER NOT NULL DEFAULT 50,parent_goal_id TEXT,dependencies_json TEXT NOT NULL,
 payload_json TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memories(
 id INTEGER PRIMARY KEY AUTOINCREMENT,memory_type TEXT NOT NULL,subject TEXT NOT NULL,
 content_json TEXT NOT NULL,importance REAL NOT NULL DEFAULT 0.5,created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decisions(
 id INTEGER PRIMARY KEY AUTOINCREMENT,decision_id TEXT UNIQUE NOT NULL,subject TEXT NOT NULL,
 decision TEXT NOT NULL,rationale TEXT NOT NULL,confidence REAL NOT NULL,
 payload_json TEXT NOT NULL,created_at TEXT NOT NULL
);
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

    def set_kv(self,k,v):
        with self.lock,self.conn() as c:
            c.execute("""INSERT INTO kv VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json,updated_at=excluded.updated_at""",
                      (k,json.dumps(v,default=str),now()))
    def get_kv(self,k,d=None):
        with self.conn() as c:
            r=c.execute("SELECT value_json FROM kv WHERE key=?",(k,)).fetchone()
            return json.loads(r["value_json"]) if r else d

    def event(self,t,source,payload,target=None):
        with self.lock,self.conn() as c:
            c.execute("INSERT INTO events(event_type,source,target,payload_json,created_at) VALUES(?,?,?,?,?)",
                      (t,source,target,json.dumps(payload,default=str),now()))
    def list_events(self,n=200):
        with self.conn() as c:
            rs=c.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?",(n,)).fetchall()
            return [dict(r)|{"payload":json.loads(r["payload_json"])} for r in rs]

    def upsert_module(self,mid,name,source,status,healthy,payload):
        with self.lock,self.conn() as c:
            c.execute("""INSERT INTO modules VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(module_id) DO UPDATE SET name=excluded.name,source=excluded.source,status=excluded.status,
            healthy=excluded.healthy,payload_json=excluded.payload_json,updated_at=excluded.updated_at""",
            (mid,name,source,status,1 if healthy else 0,json.dumps(payload,default=str),now()))
    def list_modules(self):
        with self.conn() as c:
            rs=c.execute("SELECT * FROM modules ORDER BY healthy DESC,name").fetchall()
            return [dict(r)|{"payload":json.loads(r["payload_json"])} for r in rs]

    def upsert_venture(self,vid,name,stage,score,source,payload):
        with self.lock,self.conn() as c:
            c.execute("""INSERT INTO ventures VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(venture_id) DO UPDATE SET name=excluded.name,stage=excluded.stage,score=excluded.score,
            source=excluded.source,payload_json=excluded.payload_json,updated_at=excluded.updated_at""",
            (vid,name,stage,float(score or 0),source,json.dumps(payload,default=str),now()))
    def list_ventures(self):
        with self.conn() as c:
            rs=c.execute("SELECT * FROM ventures ORDER BY score DESC,name").fetchall()
            return [dict(r)|{"payload":json.loads(r["payload_json"])} for r in rs]

    def upsert_agent(self,aid,name,role,enabled=True):
        with self.lock,self.conn() as c:
            c.execute("""INSERT INTO agents(agent_id,name,role,enabled,completed,failed,updated_at)
            VALUES(?,?,?,?,0,0,?) ON CONFLICT(agent_id) DO UPDATE SET name=excluded.name,role=excluded.role,
            enabled=excluded.enabled,updated_at=excluded.updated_at""",(aid,name,role,1 if enabled else 0,now()))
    def list_agents(self):
        with self.conn() as c: return [dict(r) for r in c.execute("SELECT * FROM agents ORDER BY name").fetchall()]
    def agent_result(self,aid,ok):
        col="completed" if ok else "failed"
        with self.lock,self.conn() as c:
            c.execute(f"UPDATE agents SET {col}={col}+1,updated_at=? WHERE agent_id=?",(now(),aid))

    def add_task(self,tid,kind,title,priority,agent,payload,max_attempts=3):
        ts=now()
        with self.lock,self.conn() as c:
            c.execute("""INSERT OR IGNORE INTO tasks(task_id,kind,title,status,priority,agent,payload_json,attempts,max_attempts,created_at,updated_at)
            VALUES(?,?,?,'QUEUED',?,?,?,0,?,?,?)""",
            (tid,kind,title,int(priority),agent,json.dumps(payload,default=str),int(max_attempts),ts,ts))
    def next_tasks(self,n=12):
        with self.conn() as c:
            rs=c.execute("SELECT * FROM tasks WHERE status='QUEUED' ORDER BY priority DESC,created_at LIMIT ?",(n,)).fetchall()
            return [dict(r)|{"payload":json.loads(r["payload_json"])} for r in rs]
    def task_state(self,tid,status,attempts_delta=0):
        with self.lock,self.conn() as c:
            c.execute("UPDATE tasks SET status=?,attempts=attempts+?,updated_at=? WHERE task_id=?",
                      (status,int(attempts_delta),now(),tid))
    def list_tasks(self,n=300):
        with self.conn() as c:
            rs=c.execute("SELECT * FROM tasks ORDER BY updated_at DESC LIMIT ?",(n,)).fetchall()
            return [dict(r)|{"payload":json.loads(r["payload_json"])} for r in rs]

    def upsert_plugin(self,pid,name,version,source,caps,enabled=True,health="OK"):
        with self.lock,self.conn() as c:
            c.execute("""INSERT INTO plugins VALUES(?,?,?,?,?,?,?,?)
            ON CONFLICT(plugin_id) DO UPDATE SET name=excluded.name,version=excluded.version,enabled=excluded.enabled,
            source=excluded.source,capabilities_json=excluded.capabilities_json,health=excluded.health,updated_at=excluded.updated_at""",
            (pid,name,version,1 if enabled else 0,source,json.dumps(caps,default=str),health,now()))
    def list_plugins(self):
        with self.conn() as c:
            rs=c.execute("SELECT * FROM plugins ORDER BY name").fetchall()
            return [dict(r)|{"capabilities":json.loads(r["capabilities_json"])} for r in rs]

    def upsert_goal(self,gid,title,venture_id,status,priority,parent_goal_id,deps,payload):
        ts=now()
        with self.lock,self.conn() as c:
            c.execute("""INSERT INTO goals VALUES(?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(goal_id) DO UPDATE SET title=excluded.title,status=excluded.status,priority=excluded.priority,
            dependencies_json=excluded.dependencies_json,payload_json=excluded.payload_json,updated_at=excluded.updated_at""",
            (gid,title,venture_id,status,int(priority),parent_goal_id,json.dumps(deps),json.dumps(payload,default=str),ts,ts))
    def list_goals(self):
        with self.conn() as c:
            rs=c.execute("SELECT * FROM goals ORDER BY priority DESC,created_at").fetchall()
            return [dict(r)|{"dependencies":json.loads(r["dependencies_json"]),"payload":json.loads(r["payload_json"])} for r in rs]

    def remember(self,mtype,subject,content,importance=0.5):
        with self.lock,self.conn() as c:
            c.execute("INSERT INTO memories(memory_type,subject,content_json,importance,created_at) VALUES(?,?,?,?,?)",
                      (mtype,subject,json.dumps(content,default=str),float(importance),now()))
    def list_memories(self,n=100):
        with self.conn() as c:
            rs=c.execute("SELECT * FROM memories ORDER BY importance DESC,id DESC LIMIT ?",(n,)).fetchall()
            return [dict(r)|{"content":json.loads(r["content_json"])} for r in rs]

    def record_decision(self,did,subject,decision,rationale,confidence,payload):
        with self.lock,self.conn() as c:
            c.execute("""INSERT OR IGNORE INTO decisions(decision_id,subject,decision,rationale,confidence,payload_json,created_at)
            VALUES(?,?,?,?,?,?,?)""",(did,subject,decision,rationale,float(confidence),json.dumps(payload,default=str),now()))
    def list_decisions(self,n=100):
        with self.conn() as c:
            rs=c.execute("SELECT * FROM decisions ORDER BY id DESC LIMIT ?",(n,)).fetchall()
            return [dict(r)|{"payload":json.loads(r["payload_json"])} for r in rs]
