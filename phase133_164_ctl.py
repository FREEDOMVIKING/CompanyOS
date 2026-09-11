#!/usr/bin/env python3
import argparse,json
from dataclasses import asdict
from companyos.runtime.project_pipeline import ProjectPipeline
from companyos.runtime.autonomous_internal_cycle import AutonomousInternalCycle
from companyos.runtime.kpi_registry import KPIRegistry
from companyos.runtime.launch_day_gate import LaunchDayGate

ap=argparse.ArgumentParser()
sub=ap.add_subparsers(dest="cmd",required=True)

p=sub.add_parser("cycle")
p.add_argument("project_id")

sub.add_parser("kpis")

p=sub.add_parser("gate")
p.add_argument("--stack-verified",action="store_true")
p.add_argument("--qa-passed",action="store_true")
p.add_argument("--project-launch-ready",action="store_true")
p.add_argument("--approval-queue-clear",action="store_true")
p.add_argument("--no-critical-blockers",action="store_true")

args=ap.parse_args()

if args.cmd=="cycle":
    print(json.dumps(asdict(AutonomousInternalCycle().run(args.project_id)),indent=2))
elif args.cmd=="kpis":
    print(json.dumps([asdict(x) for x in KPIRegistry().all()],indent=2))
else:
    r=LaunchDayGate().evaluate(
        stack_verified=args.stack_verified,
        qa_passed=args.qa_passed,
        project_launch_ready=args.project_launch_ready,
        approval_queue_clear=args.approval_queue_clear,
        no_critical_blockers=args.no_critical_blockers,
    )
    print(json.dumps(asdict(r),indent=2))
