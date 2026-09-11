#!/usr/bin/env python3
import argparse, json
from dataclasses import asdict
from companyos.runtime.launch_runtime import LaunchRuntime
from companyos.runtime.launch_health_snapshot import build_snapshot
from companyos.runtime.approval_queue import ApprovalQueue

ap=argparse.ArgumentParser()
sub=ap.add_subparsers(dest="cmd",required=True)
sub.add_parser("start")
sub.add_parser("status")
sub.add_parser("stop")
sub.add_parser("health")
sub.add_parser("approvals")
args=ap.parse_args()

lr=LaunchRuntime()
if args.cmd=="start":
    print(json.dumps(asdict(lr.start()),indent=2))
elif args.cmd=="status":
    print(json.dumps(asdict(lr.status()),indent=2))
elif args.cmd=="stop":
    print(json.dumps(asdict(lr.stop()),indent=2))
elif args.cmd=="health":
    print(json.dumps(build_snapshot(),indent=2))
else:
    items=ApprovalQueue().all()
    print(json.dumps([asdict(x) for x in items],indent=2))
