#!/usr/bin/env python3
import argparse
import json
from dataclasses import asdict

from companyos.walletintegration.runtime_control_plane import RuntimeControlPlane


ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="command", required=True)

p_start = sub.add_parser("start")
p_start.add_argument("--interval", type=float, default=15.0)
p_start.add_argument("--max-failures", type=int, default=5)

sub.add_parser("status")
sub.add_parser("stop")

args = ap.parse_args()
ctl = RuntimeControlPlane()

if args.command == "start":
    result = ctl.start(
        interval_seconds=args.interval,
        max_failures=args.max_failures,
    )
elif args.command == "stop":
    result = ctl.stop()
else:
    result = ctl.status()

print(json.dumps(asdict(result), indent=2))
