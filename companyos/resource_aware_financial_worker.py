from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json
import os
import time

from companyos.automatic_financial_queue_worker import run_once as base_run_once

STATE_ROOT = Path("companyos_runtime/resource_aware_financial_worker")
STATE_ROOT.mkdir(parents=True, exist_ok=True)
STATE_FILE = STATE_ROOT / "status.json"
LOCK_FILE = STATE_ROOT / "worker.lock"

DEFAULT_MIN_AVAILABLE_MB = int(os.getenv("COMPANYOS_FIN_QUEUE_MIN_AVAILABLE_MB", "2800"))
DEFAULT_RECOVER_MB = int(os.getenv("COMPANYOS_FIN_QUEUE_RECOVER_MB", "3400"))


def mem_available_mb() -> int:
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    kb = int(line.split()[1])
                    return kb // 1024
    except Exception:
        pass
    return 0


def scheduler_halted_for_resource_pressure() -> bool:
    candidates = [
        Path("run/autonomous_operations_health.json"),
        Path("companyos_runtime/autonomous_operations_health.json"),
        Path.home()/".companyos_runtime"/"autonomous_operations_health.json",
    ]
    for p in candidates:
        if not p.exists():
            continue
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        if d.get("halted") and d.get("last_error") == "resource_pressure":
            return True
    return False


def _write_status(data: dict[str, Any]) -> None:
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True, default=str) + "\n")
    os.replace(tmp, STATE_FILE)


def _acquire_lock() -> bool:
    try:
        fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        try:
            pid = int(LOCK_FILE.read_text().strip())
            os.kill(pid, 0)
            return False
        except Exception:
            try:
                LOCK_FILE.unlink()
            except Exception:
                pass
            return _acquire_lock()


def _release_lock() -> None:
    try:
        LOCK_FILE.unlink()
    except FileNotFoundError:
        pass


def run_resource_aware_once(max_items: int = 5) -> dict[str, Any]:
    now = time.time()
    avail = mem_available_mb()
    scheduler_pressure = scheduler_halted_for_resource_pressure()

    status = {
        "started_at": now,
        "available_memory_mb": avail,
        "minimum_available_memory_mb": DEFAULT_MIN_AVAILABLE_MB,
        "recover_memory_mb": DEFAULT_RECOVER_MB,
        "scheduler_resource_pressure": scheduler_pressure,
        "deferred": False,
        "reason": None,
        "mode": "dry_run",
        "processed": 0,
        "failed": 0,
    }

    if avail and avail < DEFAULT_MIN_AVAILABLE_MB:
        status["deferred"] = True
        status["reason"] = "memory_below_worker_threshold"
        _write_status(status)
        return status

    if scheduler_pressure and avail and avail < DEFAULT_RECOVER_MB:
        status["deferred"] = True
        status["reason"] = "scheduler_recovery_priority"
        _write_status(status)
        return status

    if not _acquire_lock():
        status["deferred"] = True
        status["reason"] = "worker_already_active"
        _write_status(status)
        return status

    try:
        r = base_run_once(max_items=max_items)
        status["processed"] = int(r.get("processed", 0))
        status["failed"] = int(r.get("failed", 0))
        status["reason"] = "worker_cycle_completed"
        status["base_result"] = r
        _write_status(status)
        return status
    finally:
        _release_lock()


def load_status() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {"status": "never_run"}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception as exc:
        return {"status": "unreadable", "error": type(exc).__name__}
