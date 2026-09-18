from __future__ import annotations

import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Lease:
    task_id: str
    owner: str
    token: str
    expires_at: float


class WorkerLeaseStore:
    """Atomic, fenced worker leases on the V33 SQLite/WAL database."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            isolation_level=None,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    def _init_schema(self) -> None:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS worker_leases(
                    task_id TEXT PRIMARY KEY,
                    owner TEXT NOT NULL,
                    token TEXT NOT NULL UNIQUE,
                    claimed_at REAL NOT NULL,
                    heartbeat_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_worker_leases_expiry
                    ON worker_leases(expires_at);
            """)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def claim(
        self,
        task_id: str,
        owner: str,
        ttl: float = 90.0,
        now: Optional[float] = None,
    ) -> Optional[Lease]:
        now = time.time() if now is None else float(now)
        ttl = max(1.0, float(ttl))
        token = uuid.uuid4().hex

        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "DELETE FROM worker_leases WHERE expires_at <= ?",
                (now,),
            )
            row = conn.execute(
                "SELECT 1 FROM worker_leases WHERE task_id=?",
                (task_id,),
            ).fetchone()
            if row is not None:
                conn.rollback()
                return None

            conn.execute(
                """INSERT INTO worker_leases
                   (task_id, owner, token, claimed_at, heartbeat_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (task_id, owner, token, now, now, now + ttl),
            )
            conn.commit()
            return Lease(task_id, owner, token, now + ttl)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def heartbeat(
        self,
        lease: Lease,
        ttl: float = 90.0,
        now: Optional[float] = None,
    ) -> bool:
        now = time.time() if now is None else float(now)
        ttl = max(1.0, float(ttl))
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.execute(
                """UPDATE worker_leases
                   SET heartbeat_at=?, expires_at=?
                   WHERE task_id=? AND owner=? AND token=? AND expires_at>?""",
                (
                    now,
                    now + ttl,
                    lease.task_id,
                    lease.owner,
                    lease.token,
                    now,
                ),
            )
            conn.commit()
            return cur.rowcount == 1
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def release(self, lease: Lease) -> bool:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.execute(
                """DELETE FROM worker_leases
                   WHERE task_id=? AND owner=? AND token=?""",
                (lease.task_id, lease.owner, lease.token),
            )
            conn.commit()
            return cur.rowcount == 1
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def recover_expired(self, now: Optional[float] = None) -> int:
        now = time.time() if now is None else float(now)
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.execute(
                "DELETE FROM worker_leases WHERE expires_at <= ?",
                (now,),
            )
            conn.commit()
            return cur.rowcount
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def active_count(self, now: Optional[float] = None) -> int:
        now = time.time() if now is None else float(now)
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM worker_leases WHERE expires_at > ?",
                (now,),
            ).fetchone()
            return int(row[0])
        finally:
            conn.close()
