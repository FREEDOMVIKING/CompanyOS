from __future__ import annotations
import json, os, tempfile
from pathlib import Path

class MissionLauncher:
    """249: adapt an HTTP provider into the Phase 228 coder-command contract."""

    def __init__(self, adapter):
        self.adapter = adapter

    def run_prompt_file(self, prompt_path):
        payload = json.loads(Path(prompt_path).read_text(encoding="utf-8"))
        return self.adapter.invoke(payload)
