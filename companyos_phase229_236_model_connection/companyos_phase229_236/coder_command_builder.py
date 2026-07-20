from __future__ import annotations
from pathlib import Path

class CoderCommandBuilder:
    """230: build the shell command that activates the CompanyOS coder bridge."""

    def build(self, project_root):
        script = Path(project_root) / "scripts" / "companyos_coder_adapter.py"
        return f"python {script}"
