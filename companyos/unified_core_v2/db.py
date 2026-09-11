
import json, sqlite3, threading
from pathlib import Path
from contextlib import contextmanager
from .util import now

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS kv (
  key TEXT PRIMARY KEY,
  value_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS modules (
  module_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  source TEXT,
  status TEXT,
  healthy INTEGER NOT NULL DEFAULT 0,
  payload_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ventures (
  venture_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  stage TEXT,
  score REAL NOT NULL DEFAULT 0,
  source TEXT,
  payload_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
  task_id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  title TEXT NOT NULL,
  status TEXT NOT NULL,
  priority INTEGER NOT NULL DEFAULT 50,
  agent TEXT,
  payload_json TEXT NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_type TEXT NOT NULL,
  source TEXT,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agents (
  agent_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  role TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1,
  completed INTEGER NOT NULL DEFAULT 0,
  failed INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL
);
"""

class StateDB:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init()

    @contextmanager
    def connect(self):
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

    def _init(self):
        with self.connect() as c:
            c.executescript(SCHEMA)

    def set_kv(self, key, value):
        with self._lock, self.connect() as c:
            c.execute(
                "INSERT INTO kv(key,value_json,updated_at) VALUES(?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json, updated_at=excluded.updated_at",
                (key, json.dumps(value, default=str), now())
            )

    def get_kv(self, key, default=None):
        with self.connect() as c:
            r = c.execute("SELECT value_json FROM kv WHERE key=?", (key,)).fetchone()
            return json.loads(r["value_json"]) if r else default

    def upsert_module(self, module_id, name, source, status, healthy, payload):
        with self._lock, self.connect() as c:
            c.execute(
                "INSERT INTO modules(module_id,name,source,status,healthy,payload_json,updated_at) VALUES(?,?,?,?,?,?,?) "
                "ON CONFLICT(module_id) DO UPDATE SET name=excluded.name,source=excluded.source,status=excluded.status,"
                "healthy=excluded.healthy,payload_json=excluded.payload_json,updated_at=excluded.updated_at",
                (module_id, name, source, status, 1 if healthy else 0, json.dumps(payload, default=str), now())
            )

    def list_modules(self):
        with self.connect() as c:
            rows = c.execute("SELECT * FROM modules ORDER BY healthy DESC,name").fetchall()
            return [dict(r) | {"payload": json.loads(r["payload_json"])} for r in rows]

    def upsert_venture(self, venture_id, name, stage, score, source, payload):
        with self._lock, self.connect() as c:
            c.execute(
                "INSERT INTO ventures(venture_id,name,stage,score,source,payload_json,updated_at) VALUES(?,?,?,?,?,?,?) "
                "ON CONFLICT(venture_id) DO UPDATE SET name=excluded.name,stage=excluded.stage,score=excluded.score,"
                "source=excluded.source,payload_json=excluded.payload_json,updated_at=excluded.updated_at",
                (venture_id, name, stage, float(score or 0), source, json.dumps(payload, default=str), now())
            )

    def list_ventures(self):
        with self.connect() as c:
            rows = c.execute("SELECT * FROM ventures ORDER BY score DESC,name").fetchall()
            return [dict(r) | {"payload": json.loads(r["payload_json"])} for r in rows]

    def upsert_agent(self, agent_id, name, role, enabled=True):
        with self._lock, self.connect() as c:
            c.execute(
                "INSERT INTO agents(agent_id,name,role,enabled,completed,failed,updated_at) VALUES(?,?,?,?,0,0,?) "
                "ON CONFLICT(agent_id) DO UPDATE SET name=excluded.name,role=excluded.role,enabled=excluded.enabled,"
                "updated_at=excluded.updated_at",
                (agent_id, name, role, 1 if enabled else 0, now())
            )

    def mark_agent_result(self, agent_id, ok):
        col = "completed" if ok else "failed"
        with self._lock, self.connect() as c:
            c.execute(f"UPDATE agents SET {col}={col}+1,updated_at=? WHERE agent_id=?", (now(), agent_id))

    def list_agents(self):
        with self.connect() as c:
            rows = c.execute("SELECT * FROM agents ORDER BY name").fetchall()
            return [dict(r) for r in rows]

    def add_task(self, task_id, kind, title, priority, agent, payload, status="QUEUED"):
        ts = now()
        with self._lock, self.connect() as c:
            c.execute(
                "INSERT OR IGNORE INTO tasks(task_id,kind,title,status,priority,agent,payload_json,attempts,created_at,updated_at) "
                "VALUES(?,?,?,?,?,?,?,0,?,?)",
                (task_id, kind, title, status, int(priority), agent, json.dumps(payload, default=str), ts, ts)
            )

    def next_tasks(self, limit=10):
        with self._lock, self.connect() as c:
            rows = c.execute(
                "SELECT * FROM tasks WHERE status='QUEUED' ORDER BY priority DESC,created_at LIMIT ?",
                (int(limit),)
            ).fetchall()
            return [dict(r) | {"payload": json.loads(r["payload_json"])} for r in rows]

    def update_task(self, task_id, status, attempts_delta=0):
        with self._lock, self.connect() as c:
            c.execute(
                "UPDATE tasks SET status=?,attempts=attempts+?,updated_at=? WHERE task_id=?",
                (status, int(attempts_delta), now(), task_id)
            )

    def list_tasks(self, limit=100):
        with self.connect() as c:
            rows = c.execute(
                "SELECT * FROM tasks ORDER BY updated_at DESC LIMIT ?", (int(limit),)
            ).fetchall()
            return [dict(r) | {"payload": json.loads(r["payload_json"])} for r in rows]

    def event(self, event_type, source, payload):
        with self._lock, self.connect() as c:
            c.execute(
                "INSERT INTO events(event_type,source,payload_json,created_at) VALUES(?,?,?,?)",
                (event_type, source, json.dumps(payload, default=str), now())
            )

    def list_events(self, limit=100):
        with self.connect() as c:
            rows = c.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
            return [dict(r) | {"payload": json.loads(r["payload_json"])} for r in rows]
