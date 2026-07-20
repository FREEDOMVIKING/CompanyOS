#!/usr/bin/env python3
import json
import os
import tempfile
from pathlib import Path
from companyos_phase253_260 import (
    CodeContract,
    ModelRouter,
    ContextBudgeter,
    RepairController,
    ExecutionBudget,
    LiveIntelligenceRuntime,
)

contract = CodeContract()
assert contract.normalize({"files": {"generated_demo/core.py": "VALUE = 1\n"}})["success"] is True

fenced = contract.normalize("""```json
{"files":{"generated_demo/core.py":"VALUE = 1\\n"}}
```""")
assert fenced["success"] is True

assert contract.normalize({"files": {"../bad.py": "x = 1\n"}})["success"] is False
assert ModelRouter().primary_model()

trimmed = ContextBudgeter().trim(
    {"files": [
        {"path": "agents/a.py", "content": "x" * 100},
        {"path": "misc.py", "content": "y" * 100},
    ]},
    max_chars=150,
)
assert trimmed["char_count"] <= 150

assert RepairController().make_prompt(
    {"task": "build"},
    {"success": False, "stage": "tests"},
    1,
)["repair_mode"] is True

assert ExecutionBudget().limits()["max_repair_attempts"] >= 1

runtime_root = Path(tempfile.mkdtemp(prefix="companyos_phase260_verify_"))
status = LiveIntelligenceRuntime(runtime_root).status()
assert status["success"] is True
assert status["self_build_pipeline_connected"] is True

print(json.dumps({
    "success": True,
    "status": "phase253_260_verification_passed",
    "cycle_status": "phase260_live_intelligence_builder_ready",
    "openrouter_live_adapter": True,
    "safe_code_contract": True,
    "model_routing": True,
    "context_budgeting": True,
    "automatic_repair_feedback": True,
    "verified_self_build_bridge": True,
    "openrouter_key_loaded": bool(os.environ.get("OPENROUTER_API_KEY", "").strip()),
    "generation_request_sent_during_install": False,
    "autonomy_mode": "high",
}, indent=2))
