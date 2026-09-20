from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from companyos.runtime.launch_health_snapshot import LaunchHealthSnapshot


class LaunchReadinessAudit:
    """
    Blocks only on actual local runtime failures or clearly tracked credential
    file types. Security-related source code names such as token.py or
    secrets_policy.py are not treated as secrets.
    """

    BLOCKED_TRACKED_SUFFIXES = (
        ".pem",
        ".key",
        ".p12",
        ".pfx",
        ".secret",
    )

    def __init__(self, root: Path | None = None):
        self.root = Path(root or (Path.home() / "companyos")).resolve()
        self.runtime_root = Path.home() / ".companyos_runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.path = self.runtime_root / "launch_readiness_audit.json"

    def _tracked_credential_files(self):
        try:
            files = subprocess.check_output(
                ["git", "ls-files"], cwd=self.root, text=True
            ).splitlines()
        except Exception:
            return []

        risky = []
        for rel in files:
            low = rel.lower()
            name = Path(low).name

            if name == ".env" or name.startswith(".env."):
                if name.endswith((".example", ".sample", ".template")):
                    continue
                risky.append(rel)
                continue

            if low.endswith(self.BLOCKED_TRACKED_SUFFIXES):
                risky.append(rel)
                continue

            if low.startswith("secrets/") and not low.endswith(
                (".md", ".txt", ".example", ".sample", ".template")
            ):
                risky.append(rel)

        return risky[:100]

    def run(self):
        snap = LaunchHealthSnapshot(self.root).build()
        runtime_health = snap["runtime"]["continuous_runtime"]
        tracked_creds = self._tracked_credential_files()

        checks = {
            "continuous_runtime_healthy": bool(runtime_health.get("healthy")),
            "service_supervisor_present": (
                self.root / "companyos/runtime/service_supervisor.py"
            ).exists(),
            "runtime_control_present": (
                self.root / "companyos/runtime/runtime_control.py"
            ).exists(),
            "storage_free_gt_1gb": float(snap["storage"]["free_gb"]) >= 1.0,
            "no_tracked_credential_files": not tracked_creds,
        }

        blocking = [name for name, ok in checks.items() if not ok]
        warnings = []
        if snap["repository"]["dirty"]:
            warnings.append(
                f"repository_has_{snap['repository']['change_count']}_working_tree_changes"
            )

        result = {
            "ready": not blocking,
            "checked_at_unix": time.time(),
            "checks": checks,
            "blocking_failures": blocking,
            "warnings": warnings,
            "tracked_credential_files": tracked_creds,
        }

        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(self.path)
        return result
