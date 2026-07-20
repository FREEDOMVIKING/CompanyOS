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
    """Deterministic adapter used for end-to-end runtime verification.

    This proves the complete build/test/integrate pipeline without pretending
    that an external coding model is configured.
    """

    def generate(self, prompt: Dict[str, Any]) -> Dict[str, Any]:
        spec = prompt["build_spec"]
        module = spec["module_name"]
        capability = spec["capability"]

        files = {
            f"{module}/__init__.py":
                "from .core import capability_status\\n\\n__all__ = ['capability_status']\\n",
            f"{module}/core.py":
                f"def capability_status():\\n"
                f"    return {{'capability': {capability!r}, 'status': 'ready'}}\\n",
            f"tests/test_{module}.py":
                f"from {module} import capability_status\\n\\n"
                f"def test_capability_status():\\n"
                f"    result = capability_status()\\n"
                f"    assert result['capability'] == {capability!r}\\n"
                f"    assert result['status'] == 'ready'\\n",
        }
        return {
            "success": True,
            "files": files,
            "metadata": {"adapter": "deterministic_scaffold"},
        }
