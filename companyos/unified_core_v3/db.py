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
 name TEXT NOT NULL,
 stage TEXT,
 score REAL NOT NULL DEFAULT 0,
 source TEXT,
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
 updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks(
 task_id TEXT PRIMARY KEY,
 kind TEXT NOT NULL,
 title TEXT NOT NULL,
 status TEXT NOT NULL,
 priority INTEGER NOT NULL DEFAULT 50,
 agent TEXT,
 payload_json TEXT NOT NULL,
 attempts INTEGER NOT NULL DEFAULT 0,
 max_attempts INTEGER NOT NULL DEFAULT 3,
 not_before TEXT,
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 event_type TEXT NOT NULL,
 source TEXT,
 target TEXT,
 payload_json TEXT NOT NULL,
 acknowledged INTEGER NOT NULL DEFAULT 0,
 created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schedules(
 schedule_id TEXT PRIMARY KEY,
 name TEXT NOT NULL,
 cadence_seconds INTEGER NOT NULL,
 task_kind TEXT NOT NULL,
 agent TEXT,
 priority INTEGER NOT NULL DEFAULT 50,
 payload_json TEXT NOT NULL,
 enabled INTEGER NOT NULL DEFAULT 1,
 last_run_at TEXT,
 next_run_at TEXT,
 updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plugins(
 plugin_id TEXT PRIMARY KEY,
 name TEXT NOT NULL,
 version TEXT NOT NULL,
 enabled INTEGER NOT NULL DEFAULT 1,
 source TEXT,
 capabilities_json TEXT NOT NULL,
 health TEXT NOT NULL DEFAULT 'UNKNOWN',
 updated_at TEXT NOT NULL
);
"""

class DB:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        with self.conn() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def conn(self):
        c = sqlite3.connect(self.path, timeout=30)
        c.row_factory = sqlite3.Row
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()

    def set_kv(self, key, value):
        with self.lock, self.conn() as c:
            c.execute("""INSERT INTO kv(key,value_json,updated_at) VALUES(?,?,?)
            ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json,updated_at=excluded.updated_at""",
            (key, json.dumps(value, default=str), now()))

    def get_kv(self, key, default=None):
        with self.conn() as c:
            r = c.execute("SELECT value_json FROM kv WHERE key=?", (key,)).fetchone()
            return json.loads(r["value_json"]) if r else default

    def event(self, event_type, source, payload, target=None):
        with self.lock, self.conn() as c:
            c.execute("INSERT INTO events(event_type,source,target,payload_json,created_at) VALUES(?,?,?,?,?)",
                      (event_type,source,target,json.dumps(payload,default=str),now()))

    def list_events(self, limit=200):
        with self.conn() as c:
            rows=c.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
            return [dict(r)|{"payload":json.loads(r["payload_json"])} for r in rows]

    def upsert_module(self, mid, name, source, status, healthy, payload):
        with self.lock, self.conn() as c:
            c.execute("""INSERT INTO modules VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(module_id) DO UPDATE SET name=excluded.name,source=excluded.source,status=excluded.status,
            healthy=excluded.healthy,payload_json=excluded.payload_json,updated_at=excluded.updated_at""",
            (mid,name,source,status,1 if healthy else 0,json.dumps(payload,default=str),now()))

    def list_modules(self):
        with self.conn() as c:
            rows=c.execute("SELECT * FROM modules ORDER BY healthy DESC,name").fetchall()
            return [dict(r)|{"payload":json.loads(r["payload_json"])} for r in rows]

    def upsert_venture(self, vid, name, stage, score, source, payload):
        with self.lock, self.conn() as c:
            c.execute("""INSERT INTO ventures VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(venture_id) DO UPDATE SET name=excluded.name,stage=excluded.stage,score=excluded.score,
            source=excluded.source,payload_json=excluded.payload_json,updated_at=excluded.updated_at""",
            (vid,name,stage,float(score or 0),source,json.dumps(payload,default=str),now()))

    def list_ventures(self):
        with self.conn() as c:
            rows=c.execute("SELECT * FROM ventures ORDER BY score DESC,name").fetchall()
            return [dict(r)|{"payload":json.loads(r["payload_json"])} for r in rows]

    def upsert_agent(self, aid, name, role, enabled=True):
        with self.lock, self.conn() as c:
            c.execute("""INSERT INTO agents(agent_id,name,role,enabled,completed,failed,updated_at)
            VALUES(?,?,?,?,0,0,?) ON CONFLICT(agent_id) DO UPDATE SET name=excluded.name,role=excluded.role,
            enabled=excluded.enabled,updated_at=excluded.updated_at""",
            (aid,name,role,1 if enabled else 0,now()))

    def list_agents(self):
        with self.conn() as c:
            return [dict(r) for r in c.execute("SELECT * FROM agents ORDER BY name").fetchall()]

    def agent_result(self, aid, ok):
        col="completed" if ok else "failed"
        with self.lock, self.conn() as c:
            c.execute(f"UPDATE agents SET {col}={col}+1,updated_at=? WHERE agent_id=?",(now(),aid))

    def add_task(self, task_id, kind, title, priority, agent, payload, max_attempts=3):
        ts=now()
        with self.lock, self.conn() as c:
            c.execute("""INSERT OR IGNORE INTO tasks(task_id,kind,title,status,priority,agent,payload_json,attempts,max_attempts,not_before,created_at,updated_at)
            VALUES(?,?,?,'QUEUED',?,?,?,0,?,NULL,?,?)""",
            (task_id,kind,title,int(priority),agent,json.dumps(payload,default=str),int(max_attempts),ts,ts))

    def next_tasks(self, limit=10):
        with self.conn() as c:
            rows=c.execute("""SELECT * FROM tasks WHERE status='QUEUED' AND
            (not_before IS NULL OR not_before<=?) ORDER BY priority DESC,created_at LIMIT ?""",(now(),limit)).fetchall()
            return [dict(r)|{"payload":json.loads(r["payload_json"])} for r in rows]

    def task_state(self, task_id, status, attempts_delta=0):
        with self.lock, self.conn() as c:
            c.execute("UPDATE tasks SET status=?,attempts=attempts+?,updated_at=? WHERE task_id=?",
                      (status,int(attempts_delta),now(),task_id))

    def requeue_failed(self, task_id):
        with self.lock, self.conn() as c:
            r=c.execute("SELECT attempts,max_attempts FROM tasks WHERE task_id=?",(task_id,)).fetchone()
            if not r: return False
            if r["attempts"] >= r["max_attempts"]:
                c.execute("UPDATE tasks SET status='DEAD',updated_at=? WHERE task_id=?",(now(),task_id))
                return False
            c.execute("UPDATE tasks SET status='QUEUED',updated_at=? WHERE task_id=?",(now(),task_id))
            return True

    def list_tasks(self, limit=200):
        with self.conn() as c:
            rows=c.execute("SELECT * FROM tasks ORDER BY updated_at DESC LIMIT ?",(limit,)).fetchall()
            return [dict(r)|{"payload":json.loads(r["payload_json"])} for r in rows]

    def upsert_schedule(self, sid, name, cadence, task_kind, agent, priority, payload, enabled=True):
        with self.lock, self.conn() as c:
            c.execute("""INSERT INTO schedules(schedule_id,name,cadence_seconds,task_kind,agent,priority,payload_json,enabled,last_run_at,next_run_at,updated_at)
            VALUES(?,?,?,?,?,?,?, ?,NULL,NULL,?)
            ON CONFLICT(schedule_id) DO UPDATE SET name=excluded.name,cadence_seconds=excluded.cadence_seconds,
            task_kind=excluded.task_kind,agent=excluded.agent,priority=excluded.priority,payload_json=excluded.payload_json,
            enabled=excluded.enabled,updated_at=excluded.updated_at""",
            (sid,name,int(cadence),task_kind,agent,int(priority),json.dumps(payload,default=str),1 if enabled else 0,now()))

    def list_schedules(self):
        with self.conn() as c:
            rows=c.execute("SELECT * FROM schedules ORDER BY name").fetchall()
            return [dict(r)|{"payload":json.loads(r["payload_json"])} for r in rows]

    def mark_schedule_run(self, sid, last_run, next_run):
        with self.lock, self.conn() as c:
            c.execute("UPDATE schedules SET last_run_at=?,next_run_at=?,updated_at=? WHERE schedule_id=?",
                      (last_run,next_run,now(),sid))

    def upsert_plugin(self, pid, name, version, source, capabilities, enabled=True, health="OK"):
        with self.lock, self.conn() as c:
            c.execute("""INSERT INTO plugins VALUES(?,?,?,?,?,?,?,?)
            ON CONFLICT(plugin_id) DO UPDATE SET name=excluded.name,version=excluded.version,enabled=excluded.enabled,
            source=excluded.source,capabilities_json=excluded.capabilities_json,health=excluded.health,updated_at=excluded.updated_at""",
            (pid,name,version,1 if enabled else 0,source,json.dumps(capabilities,default=str),health,now()))

    def list_plugins(self):
        with self.conn() as c:
            rows=c.execute("SELECT * FROM plugins ORDER BY name").fetchall()
            return [dict(r)|{"capabilities":json.loads(r["capabilities_json"])} for r in rows]
