from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict


class IntegrationGate:
    """217: final live-tree verification after promotion."""

    def verify_live(self, project_root: str | Path, targeted_test: str | None = None) -> Dict[str, Any]:
        root = Path(project_root)

        compile_p = subprocess.run(
            [sys.executable, "-m", "compileall", "-q", "."],
            cwd=str(root),
            text=True,
            capture_output=True,
            timeout=240,
            check=False,
        )
        if compile_p.returncode != 0:
            return {
                "success": False,
                "stage": "live_compile",
                "stderr": compile_p.stderr[-12000:],
            }

        cmd = [sys.executable, "-m", "pytest", "-q", "--disable-warnings"]
        if targeted_test:
            cmd.append(targeted_test)

        test_p = subprocess.run(
            cmd,
            cwd=str(root),
            text=True,
            capture_output=True,
            timeout=300,
            check=False,
        )
        return {
            "success": test_p.returncode == 0,
            "stage": "live_tests",
            "stdout": test_p.stdout[-12000:],
            "stderr": test_p.stderr[-12000:],
        }
