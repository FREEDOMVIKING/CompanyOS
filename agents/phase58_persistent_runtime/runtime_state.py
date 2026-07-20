#!/usr/bin/env python3

import json
import os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase58"
STATE_FILE = MEMORY / "persistent_runtime_state.json"

MEMORY.mkdir(parents=True, exist_ok=True)


def now():
    return datetime.now(timezone.utc).isoformat()


def default_state():
    return {
        "phase": 58,
        "status": "stopped",
        "pid": None,
        "started_at": None,
        "stopped_at": None,
        "last_heartbeat": None,
        "restart_count": 0,
        "cycles_this_session": 0,
        "last_error": None,
        "stop_requested": False,
    }


def load_state():
    if not STATE_FILE.exists():
        state = default_state()
        save_state(state)
        return state

    try:
        state = json.loads(STATE_FILE.read_text())
    except Exception:
        state = default_state()
        save_state(state)

    return state


def save_state(state):
    state["updated_at"] = now()
    STATE_FILE.write_text(json.dumps(state, indent=2))
    return state


def mark_started():
    state = load_state()
    state["status"] = "running"
    state["pid"] = os.getpid()
    state["started_at"] = now()
    state["stopped_at"] = None
    state["last_heartbeat"] = now()
    state["cycles_this_session"] = 0
    state["last_error"] = None
    state["stop_requested"] = False
    return save_state(state)


def heartbeat():
    state = load_state()
    state["last_heartbeat"] = now()
    return save_state(state)


def mark_stopped():
    state = load_state()
    state["status"] = "stopped"
    state["pid"] = None
    state["stopped_at"] = now()
    state["stop_requested"] = False
    return save_state(state)


def request_stop():
    state = load_state()
    state["stop_requested"] = True
    state["status"] = "stop_requested"
    return save_state(state)


def status():
    return {
        "success": True,
        "status": "phase58_persistent_runtime_state",
        "state": load_state(),
    }


if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
