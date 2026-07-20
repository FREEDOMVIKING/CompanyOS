#!/usr/bin/env python3

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path.cwd()
MEM = ROOT / "ceo_memory/phase51"

PLANS = MEM / "execution_plans.json"
QUEUE = MEM / "task_queue.json"

PLANS_BAK = ROOT / "phase51_plans_e2e_backup.json"
QUEUE_BAK = ROOT / "phase51_queue_e2e_backup.json"

shutil.copy2(PLANS, PLANS_BAK)

if QUEUE.exists():
    shutil.copy2(QUEUE, QUEUE_BAK)

plans = json.loads(PLANS.read_text())

test_plan = {
    "plan_id": "phase52-e2e-test-plan",
    "opportunity_id": "phase52-e2e-test-opportunity",
    "objective": "Validate Phase 51 to Phase 52 specialist execution",
    "milestones": [
        {
            "id": "M1",
            "name": "Integration validation",
            "status": "pending"
        }
    ],
    "tasks": [
        {
            "task_id": "phase52-e2e-test-T1",
            "milestone": "M1",
            "title": "Validate Phase 52 end-to-end specialist handoff",
            "specialist_role": "research_agent",
            "depends_on": [],
            "action_class": "reversible_internal",
            "status": "pending"
        }
    ],
    "status": "planned"
}

plans.setdefault("plans", []).append(test_plan)
PLANS.write_text(json.dumps(plans, indent=2))

try:
    print("===== DISPATCH =====")
    subprocess.run(
        ["python", "companyos/phase51ctl", "dispatch"],
        check=True
    )

    print("\n===== EXECUTE THROUGH PHASE 52 =====")
    subprocess.run(
        ["python", "companyos/phase51ctl", "execute-next"],
        check=True
    )

    print("\n===== PHASE 52 STATUS =====")
    subprocess.run(
        ["python", "agents/phase52_specialist_runtime/runtime.py"],
        check=True
    )

finally:
    shutil.copy2(PLANS_BAK, PLANS)

    if QUEUE_BAK.exists():
        shutil.copy2(QUEUE_BAK, QUEUE)
    elif QUEUE.exists():
        QUEUE.unlink()

    print("\nORIGINAL PHASE 51 PLAN/QUEUE STATE RESTORED")
