#!/usr/bin/env python3
import argparse, json, uuid
from dataclasses import asdict

from companyos.runtime.project_pipeline import ProjectPipeline
from companyos.runtime.operations_loop import OperationsLoop
from companyos.runtime.launch_dashboard import dashboard
from companyos.runtime.launch_readiness import LaunchReadinessEvaluator

ap=argparse.ArgumentParser()
sub=ap.add_subparsers(dest="cmd",required=True)

p=sub.add_parser("create-project")
p.add_argument("title")
p.add_argument("objective")

p=sub.add_parser("cycle-project")
p.add_argument("project_id")

p=sub.add_parser("project-status")
p.add_argument("project_id")

p=sub.add_parser("launch-readiness")
p.add_argument("project_id")

sub.add_parser("dashboard")
args=ap.parse_args()

if args.cmd=="create-project":
    r=ProjectPipeline().create(title=args.title,objective=args.objective)
    print(json.dumps(asdict(r),indent=2))
elif args.cmd=="cycle-project":
    r=OperationsLoop().cycle(args.project_id)
    print(json.dumps(asdict(r),indent=2))
elif args.cmd=="project-status":
    r=ProjectPipeline().load(args.project_id)
    print(json.dumps(asdict(r),indent=2))
elif args.cmd=="launch-readiness":
    r=ProjectPipeline().load(args.project_id)
    report=LaunchReadinessEvaluator().evaluate(
        project_stage=r.stage,
        blockers=r.blockers,
        artifacts_count=len(r.artifacts)
    )
    print(json.dumps(asdict(report),indent=2))
else:
    print(json.dumps(dashboard(),indent=2))
