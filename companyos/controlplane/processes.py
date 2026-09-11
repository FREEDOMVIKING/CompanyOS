import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional

def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def start_module(module: str, log_path: Path, env: Optional[Dict[str, str]] = None) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(log_path, "a")
    proc = subprocess.Popen(
        [sys.executable, "-m", module],
        stdout=handle,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        env={**os.environ, **(env or {})},
        close_fds=True,
    )
    return proc.pid

def stop_pid(pid: int, timeout_seconds: float = 5.0) -> bool:
    import time
    if not pid_alive(pid):
        return True
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return True
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if not pid_alive(pid):
            return True
        time.sleep(0.1)
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        pass
    return not pid_alive(pid)
