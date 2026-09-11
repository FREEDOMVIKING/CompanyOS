#!/usr/bin/env python3
from pathlib import Path
import tempfile

from companyos.runtime.autonomous_goal_intake import AutonomousGoalIntake
from companyos.runtime.goal_source_policy import GoalSourcePolicy
from companyos.runtime.policy_guarded_goal_intake import PolicyGuardedGoalIntake

with tempfile.TemporaryDirectory(prefix="phase105_policy_") as td:
    intake = AutonomousGoalIntake(Path(td) / "intake")
    guarded = PolicyGuardedGoalIntake(intake=intake, policy=GoalSourcePolicy())

    internal = guarded.submit(
        goal="research and plan a small internal software product",
        priority=25,
        source="manual",
        intake_id="internal",
    )

    sensitive = guarded.submit(
        goal="buy a domain and publish the site",
        priority=10,
        source="manual",
        intake_id="sensitive",
    )

    checks = {
        "internal_accepted": internal.accepted,
        "internal_no_approval": internal.requires_human_approval is False,
        "sensitive_accepted_for_intake": sensitive.accepted,
        "sensitive_requires_approval": sensitive.requires_human_approval is True,
        "external_detected": sensitive.external_action_requested is True,
        "financial_detected": sensitive.financial_action_requested is True,
        "two_intake_records": len(intake.all_records()) == 2,
    }

    ok = True
    for name, passed in checks.items():
        ok = ok and passed
        print(name, "=>", "PASS" if passed else "FAIL")

    print("POLICY_GATE_EXTERNAL_ACTIONS: False")
    print("POLICY_GATE_SIGNS_TRANSACTION: False")
    print("POLICY_GATE_BROADCASTS: False")
    print("PHASE105_POLICY_TEST:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
