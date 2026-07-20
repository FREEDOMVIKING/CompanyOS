#!/usr/bin/env python3

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from agents.phase58_persistent_runtime.runtime_manager import (
    status as runtime_status,
    start as runtime_start,
)


ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase59"
STATE_FILE = MEMORY / "watchdog_state.json"

MEMORY.mkdir(parents=True, exist_ok=True)


def now():
    return datetime.now(timezone.utc).isoformat()


def load_state():
    if not STATE_FILE.exists():
        return {
            "phase": 59,
            "checks": 0,
            "restart_attempts": 0,
            "last_check": None,
            "last_action": None,
        }

    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {
            "phase": 59,
            "checks": 0,
            "restart_attempts": 0,
            "last_check": None,
            "last_action": "state_recovered",
        }


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))
    return state


def watchdog_check(auto_restart=True):
    state = load_state()
    state["checks"] = state.get("checks", 0) + 1
    state["last_check"] = now()

    runtime = runtime_status()
    alive = bool(runtime.get("process_alive"))

    if alive:
        state["last_action"] = "runtime_healthy"
        save_state(state)

        return {
            "success": True,
            "status": "phase59_runtime_healthy",
            "process_alive": True,
            "runtime": runtime,
            "watchdog_state": state,
        }

    if not auto_restart:
        state["last_action"] = "runtime_down_detected"
        save_state(state)

        return {
            "success": False,
            "status": "phase59_runtime_down",
            "process_alive": False,
            "runtime": runtime,
            "watchdog_state": state,
        }

    state["restart_attempts"] = state.get("restart_attempts", 0) + 1
    restart = runtime_start()

    state["last_action"] = "restart_requested"
    state["last_restart"] = now()
    save_state(state)

    return {
        "success": bool(restart.get("success")),
        "status": "phase59_restart_requested",
        "restart": restart,
        "watchdog_state": state,
    }


if __name__ == "__main__":
    print(json.dumps(watchdog_check(auto_restart=True), indent=2))
