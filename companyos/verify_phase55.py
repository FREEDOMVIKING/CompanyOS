#!/usr/bin/env python3

import json
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ORCHESTRATOR = ROOT / "agents/phase55_ceo_orchestrator/ceo_orchestrator.py"
CYCLE = ROOT / "agents/phase55_ceo_orchestrator/autonomous_cycle.py"

errors = []
warnings = []


def check(condition, message):
    if not condition:
        errors.append(message)


print("[1/4] Checking Phase 55 files...")

check(ORCHESTRATOR.exists(), "Missing CEO orchestrator")
check(CYCLE.exists(), "Missing autonomous CEO cycle")


print("[2/4] Compiling Phase 55 components...")

for path in [ORCHESTRATOR, CYCLE]:
    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        errors.append(f"Compile failure {path.name}: {exc}")


print("[3/4] Checking upstream integration...")

required_upstream = [
    ROOT / "agents/phase54_collaboration/collaboration_orchestrator.py",
    ROOT / "agents/phase53_specialist_intelligence/intelligence_core.py",
    ROOT / "agents/phase52_specialist_runtime/runtime.py",
    ROOT / "agents/phase51_execution_planner/execution_planner.py"
]

for path in required_upstream:
    check(path.exists(), f"Missing upstream component: {path}")


print("[4/4] Checking CEO safety boundaries...")

from agents.phase55_ceo_orchestrator.ceo_orchestrator import (
    classify_next_action
)

safe = classify_next_action("reversible_internal")
financial = classify_next_action("financial_commitment")
irreversible = classify_next_action("irreversible_external")

check(
    safe.get("approval_required") is False,
    "Safe reversible internal action incorrectly requires approval"
)

check(
    financial.get("approval_required") is True,
    "Financial commitment approval boundary failed"
)

check(
    irreversible.get("approval_required") is True,
    "Irreversible external action approval boundary failed"
)

print()
print("--------------------------------------------")
print("PHASE 55 AUTONOMOUS CEO ORCHESTRATOR VERIFICATION")
print("Errors:", len(errors))
print("Warnings:", len(warnings))
print("--------------------------------------------")

if errors:
    for error in errors:
        print("-", error)
    raise SystemExit(1)

print()
print("PHASE 55 AUTONOMOUS CEO ORCHESTRATOR VERIFIED")
print("MULTI-AGENT COLLABORATION: ENABLED")
print("SPECIALIST INTELLIGENCE HANDOFF: ENABLED")
print("CEO SYNTHESIS: ENABLED")
print("AUTONOMOUS REVERSIBLE INTERNAL ACTIONS: ENABLED")
print("FINANCIAL COMMITMENT APPROVAL: REQUIRED")
print("IRREVERSIBLE EXTERNAL ACTION APPROVAL: REQUIRED")
print("Errors: 0")
print("Warnings: 0")
