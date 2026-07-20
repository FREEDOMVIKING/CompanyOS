from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, List


class ToolExecutor:
    """214: bounded local tool executor for autonomous build work."""

    ALLOWED = {
        "python",
        "python3",
        "pytest",
        "git",
    }

    def run(self, command: List[str], cwd: str | Path, timeout: int = 180) -> Dict[str, Any]:
        if not command:
            return {"success": False, "reason": "empty_command"}

        executable = Path(command[0]).name
        if executable not in self.ALLOWED:
            return {
                "success": False,
                "reason": f"command_not_allowed:{executable}",
            }

        p = subprocess.run(
            command,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "success": p.returncode == 0,
            "returncode": p.returncode,
            "stdout": p.stdout[-12000:],
            "stderr": p.stderr[-12000:],
        }
