from __future__ import annotations
import json, sqlite3, time
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

class DurableExecutionKernel:
    def __init__(self, runtime_root=None):
        self.runtime_root=runtime_root or Path.home()/".companyos_runtime"
        self.runtime_root.mkdir(parents=True,exist_ok=True)
        self.db_path=self.runtime_root/"execution_kernel.sqlite3"
        self.journal_mode=self._configure_journal_mode()
        self._init()

    def _configure_journal_mode(self):
        """
        Negotiate WAL once at kernel startup.

        Multiple CompanyOS processes may initialize concurrently. Changing
        SQLite journal mode on every connection can trigger locking-protocol
        failures. If WAL cannot be enabled because another process/filesystem
        rejects the transition, keep the database's existing journal mode.
        """
        c=sqlite3.connect(
            self.db_path,
            timeout=30,
            isolation_level=None,
        )

        try:
            c.execute("PRAGMA busy_timeout=30000")

            try:
                row=c.execute(
                    "PRAGMA journal_mode=WAL"
                ).fetchone()

                return (
                    str(row[0]).lower()
                    if row
                    else "unknown"
                )

            except sqlite3.OperationalError as exc:
                msg=str(exc).lower()

                recoverable=(
                    "locking protocol" in msg
                    or "database is locked" in msg
                    or "database table is locked" in msg
                )

                if not recoverable:
                    raise

                # Close this connection and let normal connections use
                # whatever journal mode SQLite already has configured.
                return "existing"

        finally:
            c.close()

    def connect(self):
        c=sqlite3.connect(
            self.db_path,
            timeout=30,
            isolation_level=None,
        )
        c.row_factory=sqlite3.Row

        # These are connection-local and safe to configure each time.
        c.execute("PRAGMA busy_timeout=30000")
        c.execute("PRAGMA synchronous=FULL")

        return c

    @contextmanager
    def tx(self):
        c=self.connect()
        try:
            c.execute("BEGIN IMMEDIATE"); yield c; c.commit()
        except Exception:
            c.rollback(); raise
        finally: c.close()

    def _init(self):
        with self.tx() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS tasks(
              task_id TEXT PRIMARY KEY,idempotency_key TEXT,task_type TEXT,priority INTEGER,
              state TEXT,assigned_agent TEXT,attempts INTEGER,max_attempts INTEGER,
              created_at_unix REAL,updated_at_unix REAL,next_attempt_unix REAL,
              goal_id TEXT,stage TEXT,depends_on_stage TEXT,payload_json TEXT,result_json TEXT,last_error TEXT);
            CREATE UNIQUE INDEX IF NOT EXISTS ix_idem ON tasks(idempotency_key)
              WHERE idempotency_key IS NOT NULL AND idempotency_key<>'';
            CREATE INDEX IF NOT EXISTS ix_ready ON tasks(state,next_attempt_unix,priority DESC,created_at_unix);
            CREATE INDEX IF NOT EXISTS ix_stage ON tasks(goal_id,stage,state);
            """)

    def upsert(self,t):
        d=asdict(t); p=d.get("payload") if isinstance(d.get("payload"),dict) else {}
        with self.tx() as c:
            c.execute("""INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(task_id) DO UPDATE SET
            idempotency_key=excluded.idempotency_key,task_type=excluded.task_type,priority=excluded.priority,
            state=excluded.state,assigned_agent=excluded.assigned_agent,attempts=excluded.attempts,
            max_attempts=excluded.max_attempts,updated_at_unix=excluded.updated_at_unix,
            next_attempt_unix=excluded.next_attempt_unix,goal_id=excluded.goal_id,stage=excluded.stage,
            depends_on_stage=excluded.depends_on_stage,payload_json=excluded.payload_json,
            result_json=excluded.result_json,last_error=excluded.last_error""",
            (d["task_id"],d.get("idempotency_key") or "",d["task_type"],d["priority"],d["state"],
             d.get("assigned_agent"),d["attempts"],d["max_attempts"],d["created_at_unix"],d["updated_at_unix"],
             d["next_attempt_unix"],p.get("goal_id"),p.get("stage"),p.get("depends_on_stage"),
             json.dumps(p,default=str),None if d.get("result") is None else json.dumps(d["result"],default=str),
             d.get("last_error")))

    def idempotent_task(self,key):
        if not key:return None
        c=self.connect()
        try:r=c.execute("SELECT task_id FROM tasks WHERE idempotency_key=? LIMIT 1",(key,)).fetchone()
        finally:c.close()
        return r["task_id"] if r else None

    def completed_stage(self,goal,stage):
        c=self.connect()
        try:r=c.execute("SELECT 1 FROM tasks WHERE goal_id=? AND stage=? AND state='COMPLETED' LIMIT 1",(goal,stage)).fetchone()
        finally:c.close()
        return bool(r)

    def counts(self):
        c=self.connect()
        try: rows=c.execute("SELECT state,count(*) n FROM tasks GROUP BY state").fetchall()
        finally:c.close()
        return {r["state"]:r["n"] for r in rows}

    def import_queue(self,q):
        ok=bad=0
        for f in q.root.glob("*.json"):
            try:self.upsert(q.load(f.stem));ok+=1
            except Exception:bad+=1
        return {"imported":ok,"invalid":bad}
