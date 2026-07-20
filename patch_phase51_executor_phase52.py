from pathlib import Path

p = Path("agents/phase51_execution_planner/task_executor.py")
s = p.read_text()

old_import = '''from datetime import datetime, timezone
'''

new_import = '''from datetime import datetime, timezone

from agents.phase52_specialist_runtime.runtime import (
    run_specialist as phase52_run_specialist
)

from agents.phase52_specialist_runtime.context_bridge import (
    build_context
)
'''

if old_import not in s:
    raise SystemExit("datetime import block not found")

s = s.replace(old_import, new_import, 1)

old_func = '''def run_specialist(task):
    role = task.get("specialist_role")
    title = task.get("title")

    return {
        "success": True,
        "specialist_role": role,
        "task_title": title,
        "execution_mode": "internal_reversible",
        "summary": (
            f"Task processed by {role}. "
            f"Structured result generated for: {title}"
        ),
        "completed_at": now()
    }
'''

new_func = '''def run_specialist(task):
    role = task.get("specialist_role")
    title = task.get("title")
    plan_id = task.get("plan_id")
    task_id = task.get("task_id")

    context = build_context(
        plan_id=plan_id,
        task_id=task_id
    )

    result = phase52_run_specialist(
        role=role,
        task=title,
        context=context
    )

    return {
        "success": result.get("success", False),
        "specialist_role": role,
        "task_title": title,
        "execution_mode": "phase52_specialist_runtime",
        "phase52_result": result,
        "completed_at": now()
    }
'''

if old_func not in s:
    raise SystemExit("old run_specialist function not found")

s = s.replace(old_func, new_func, 1)

p.write_text(s)

print("PHASE 51 EXECUTOR CONNECTED TO PHASE 52")
