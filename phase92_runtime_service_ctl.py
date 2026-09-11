#!/usr/bin/env python3
import argparse
import json
from dataclasses import asdict

from companyos.walletintegration.runtime_service_manager import RuntimeServiceManager

ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="command", required=True)

p_start = sub.add_parser("start")
p_start.add_argument("--supervisor-interval", type=float, default=15.0)
p_start.add_argument("--watchdog-check-every", type=float, default=30.0)
p_start.add_argument("--max-failures", type=int, default=5)
p_start.add_argument("--restart-backoff", type=float, default=5.0)

sub.add_parser("status")
sub.add_parser("stop")

args = ap.parse_args()
mgr = RuntimeServiceManager()

if args.command == "start":
    result = mgr.start(
        supervisor_interval=args.supervisor_interval,
        watchdog_check_every=args.watchdog_check_every,
        max_failures=args.max_failures,
        restart_backoff=args.restart_backoff,
    )
elif args.command == "stop":
    result = mgr.stop()
else:
    result = mgr.status()

print(json.dumps(asdict(result), indent=2))
