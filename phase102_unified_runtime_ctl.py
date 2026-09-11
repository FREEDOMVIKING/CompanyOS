#!/usr/bin/env python3
import argparse
import json
from dataclasses import asdict

from companyos.runtime.unified_runtime_stack_manager import UnifiedRuntimeStackManager

ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="command", required=True)

p_start = sub.add_parser("start")
p_start.add_argument("--financial-supervisor-interval", type=float, default=15.0)
p_start.add_argument("--watchdog-check-every", type=float, default=30.0)
p_start.add_argument("--financial-max-failures", type=int, default=5)
p_start.add_argument("--restart-backoff", type=float, default=5.0)
p_start.add_argument("--ceo-interval", type=float, default=10.0)
p_start.add_argument("--ceo-max-failures", type=int, default=5)

sub.add_parser("status")
sub.add_parser("stop")

args = ap.parse_args()
mgr = UnifiedRuntimeStackManager()

if args.command == "start":
    result = mgr.start(
        financial_supervisor_interval=args.financial_supervisor_interval,
        watchdog_check_every=args.watchdog_check_every,
        financial_max_failures=args.financial_max_failures,
        restart_backoff=args.restart_backoff,
        ceo_interval=args.ceo_interval,
        ceo_max_failures=args.ceo_max_failures,
    )
elif args.command == "stop":
    result = mgr.stop()
else:
    result = mgr.status()

print(json.dumps(asdict(result), indent=2))
