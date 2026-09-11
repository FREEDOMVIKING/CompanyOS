#!/usr/bin/env python3
from __future__ import annotations
import argparse, json

from companyos.canonicalproduction import CanonicalProductionRuntime

def main():
    ap = argparse.ArgumentParser(description="CompanyOS Canonical Production Runtime")
    sub = ap.add_subparsers(dest="command", required=True)

    sub.add_parser("start")
    sub.add_parser("stop")
    sub.add_parser("status")
    sub.add_parser("health")
    sub.add_parser("test")

    p_once = sub.add_parser("once")
    p_once.add_argument(
        "--objective",
        default="Run one internal CompanyOS production validation cycle"
    )

    args = ap.parse_args()
    rt = CanonicalProductionRuntime()

    if args.command == "start":
        out = rt.start()
    elif args.command == "stop":
        out = rt.stop()
    elif args.command in ("status", "health"):
        out = rt.status()
    elif args.command == "test":
        out = rt.test()
    else:
        out = rt.once(args.objective)

    print(json.dumps(out, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
