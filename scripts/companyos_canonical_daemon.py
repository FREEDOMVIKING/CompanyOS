#!/usr/bin/env python3
from __future__ import annotations
import argparse
from companyos.canonicaldaemon import CanonicalCompanyOSDaemon

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--heartbeat-interval", type=float, default=15.0)
    args = ap.parse_args()
    return CanonicalCompanyOSDaemon(
        heartbeat_interval=args.heartbeat_interval
    ).run_forever()

if __name__ == "__main__":
    raise SystemExit(main())
