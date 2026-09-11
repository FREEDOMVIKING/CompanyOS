#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from companyos.finallaunch import FinalLaunchController

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("preflight")
    sub.add_parser("status")
    sub.add_parser("safe")

    t = sub.add_parser("trial")
    t.add_argument("--max-single", type=float, required=True)
    t.add_argument("--max-daily", type=float, required=True)
    t.add_argument("--confirm", required=True)

    f = sub.add_parser("full")
    f.add_argument("--max-single", type=float, required=True)
    f.add_argument("--max-daily", type=float, required=True)
    f.add_argument("--max-failures", type=int, default=3)
    f.add_argument("--confirm", required=True)

    args = ap.parse_args()
    ctl = FinalLaunchController()

    if args.cmd == "preflight":
        out = ctl.preflight()
    elif args.cmd == "status":
        out = {"profile": ctl.current_profile(), "preflight": ctl.preflight()}
    elif args.cmd == "safe":
        out = ctl.set_safe()
    elif args.cmd == "trial":
        out = ctl.set_trial(args.max_single, args.max_daily, args.confirm)
    else:
        out = ctl.set_full(args.max_single, args.max_daily, args.max_failures, args.confirm)

    print(json.dumps(out, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
