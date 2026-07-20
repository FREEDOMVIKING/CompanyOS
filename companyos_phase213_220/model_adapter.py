from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict


class ModelAdapter:
    """213: pluggable coding/reasoning-model adapter.

    External model use is configured with COMPANYOS_CODER_CMD.
    The command receives the prompt-file path as its final argument and must
    print JSON describing files to create:
      {"files": {"relative/path.py": "content", ...}}
    """

    def __init__(self, command: str | None = None):
        self.command = command or os.environ.get("COMPANYOS_CODER_CMD", "").strip()

    @property
    def available(self) -> bool:
        return bool(self.command)

    def generate(self, prompt: Dict[str, Any]) -> Dict[str, Any]:
        if not self.available:
            return {
                "success": False,
                "reason": "coder_command_not_configured",
                "files": {},
            }

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(prompt, f, indent=2)
            prompt_path = f.name

        try:
            cmd = shlex.split(self.command) + [prompt_path]
            p = subprocess.run(
                cmd,
                text=True,
                capture_output=True,
                timeout=300,
                check=False,
            )
            if p.returncode != 0:
                return {
                    "success": False,
                    "reason": "coder_command_failed",
                    "stderr": p.stderr[-8000:],
                    "files": {},
                }
            try:
                data = json.loads(p.stdout)
            except Exception as exc:
                return {
                    "success": False,
                    "reason": f"invalid_coder_json:{exc}",
                    "raw_output": p.stdout[-8000:],
                    "files": {},
                }

            files = data.get("files", {})
            if not isinstance(files, dict):
                files = {}

            return {
                "success": bool(files),
                "files": files,
                "metadata": data.get("metadata", {}),
            }
        finally:
            try:
                Path(prompt_path).unlink(missing_ok=True)
            except Exception:
                pass


class DeterministicScaffoldAdapter:
    """Deterministic adapter for end-to-end self-build verification."""

    def generate(self, prompt):
        spec = prompt["build_spec"]
        module = spec["module_name"]
        capability = spec["capability"]

        init_code = (
            "from .core import capability_status\n"
            "\n"
            "__all__ = ['capability_status']\n"
        )

        core_code = (
            "def capability_status():\n"
            f"    return {{'capability': {capability!r}, 'status': 'ready'}}\n"
        )

        test_code = (
            f"from {module} import capability_status\n"
            "\n"
            "def test_capability_status():\n"
            "    result = capability_status()\n"
            f"    assert result['capability'] == {capability!r}\n"
            "    assert result['status'] == 'ready'\n"
        )

        return {
            "success": True,
            "files": {
                f"{module}/__init__.py": init_code,
                f"{module}/core.py": core_code,
                f"tests/test_{module}.py": test_code,
            },
            "metadata": {
                "adapter": "deterministic_scaffold"
            },
        }
