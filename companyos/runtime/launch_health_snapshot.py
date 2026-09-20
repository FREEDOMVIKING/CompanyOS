from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

from companyos.runtime.runtime_status import RuntimeStatus


class LaunchHealthSnapshot:
    def __init__(self, root: Path | None = None):
        self.root = Path(root or (Path.home() / "companyos")).resolve()
        self.runtime_root = Path.home() / ".companyos_runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.path = self.runtime_root / "launch_health_snapshot.json"

    def build(self):
        usage = shutil.disk_usage(self.root)
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        changes = [x for x in result.stdout.splitlines() if x.strip()]

        snapshot = {
            "checked_at_unix": time.time(),
            "runtime": RuntimeStatus(self.root).status(),
            "repository": {
                "git_ok": result.returncode == 0,
                "dirty": bool(changes),
                "change_count": len(changes),
                "changes": changes[:100],
            },
            "storage": {
                "free_gb": round(usage.free / (1024 ** 3), 2),
                "total_gb": round(usage.total / (1024 ** 3), 2),
            },
        }

        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(snapshot, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )
        tmp.replace(self.path)
        return snapshot
