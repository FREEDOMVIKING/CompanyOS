from pathlib import Path

p = Path("agents/phase52_specialist_runtime/runtime.py")
s = p.read_text()

import_line = (
    "from agents.phase53_specialist_intelligence.intelligence_core "
    "import analyze as phase53_analyze\n"
)

if import_line not in s:
    marker = "from datetime import datetime, timezone\n"

    if marker not in s:
        raise SystemExit("datetime import marker not found")

    s = s.replace(
        marker,
        marker + "\n" + import_line,
        1
    )

old = '''    result = {
        "success": True,
        "status": "phase52_specialist_complete",
        "role": role,
        "task": task,
        "mission": role_prompts[role],
        "context_received": context,
        "output": {
            "summary": f"{role} completed structured analysis for: {task}",
            "recommendations": [],
            "risks": [],
            "next_inputs": []
        },
        "completed_at": now()
    }
'''

new = '''    phase53_result = phase53_analyze(
        role=role,
        task=task,
        context=context
    )

    if not phase53_result.get("success", False):
        return {
            "success": False,
            "status": "phase52_phase53_execution_failed",
            "role": role,
            "task": task,
            "phase53_result": phase53_result
        }

    artifact = phase53_result.get("artifact", {})
    analysis = artifact.get("analysis", {})

    result = {
        "success": True,
        "status": "phase52_specialist_complete",
        "role": role,
        "task": task,
        "mission": role_prompts[role],
        "context_received": context,
        "output": {
            "summary": f"{role} completed Phase 53 intelligence analysis for: {task}",
            "findings": analysis.get("findings", []),
            "recommendations": analysis.get("recommendations", []),
            "risks": analysis.get("risks", []),
            "assumptions": analysis.get("assumptions", []),
            "next_inputs": analysis.get("next_inputs", [])
        },
        "phase53_artifact": artifact,
        "completed_at": now()
    }
'''

if old not in s:
    raise SystemExit("Phase 52 result block not found - no changes made")

s = s.replace(old, new, 1)
p.write_text(s)

print("PHASE 52 -> PHASE 53 INTELLIGENCE BRIDGE PATCHED")
