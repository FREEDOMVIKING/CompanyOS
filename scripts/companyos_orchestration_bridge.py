#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from companyos.canonicalorchestration import CanonicalOrchestrationBridge, GoalRequest

def main():
    ap = argparse.ArgumentParser(description="CompanyOS Canonical Orchestration Bridge")
    sub = ap.add_subparsers(dest="command", required=True)

    sub.add_parser("status")

    p_run = sub.add_parser("run-goal")
    p_run.add_argument("--objective", required=True)
    p_run.add_argument("--context-json", default="{}")
    p_run.add_argument("--goal-id", default="")

    args = ap.parse_args()
    bridge = CanonicalOrchestrationBridge()

    if args.command == "status":
        print(json.dumps(bridge.status(), indent=2, sort_keys=True))
        return 0

    context = json.loads(args.context_json)
    result = bridge.run_goal(
        GoalRequest(
            objective=args.objective,
            context=context,
            goal_id=args.goal_id,
        )
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
