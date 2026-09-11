#!/usr/bin/env python3
import argparse
import time

from companyos.walletintegration.runtime_watchdog import RuntimeWatchdog

ap = argparse.ArgumentParser()
ap.add_argument("--check-every", type=float, default=30.0)
ap.add_argument("--runtime-interval", type=float, default=15.0)
ap.add_argument("--max-failures", type=int, default=5)
ap.add_argument("--restart-backoff", type=float, default=5.0)
args = ap.parse_args()

watchdog = RuntimeWatchdog(
    restart_backoff_seconds=args.restart_backoff,
    max_restarts_per_window=5,
    restart_window_seconds=600,
)

print("COMPANYOS_RUNTIME_WATCHDOG: STARTED")
print("WATCHDOG_BROADCASTS: False")

try:
    while True:
        result = watchdog.evaluate_once(
            interval_seconds=args.runtime_interval,
            max_failures=args.max_failures,
        )
        print(
            f"ACTION={result.action} "
            f"REASON={result.reason} "
            f"RUNNING={result.running} "
            f"READY={result.ready} "
            f"RPC_OK={result.rpc_ok} "
            f"STALE={result.stale} "
            f"UNRESOLVED={result.unresolved_records} "
            f"RESTARTS={result.restart_count}"
        )
        time.sleep(max(5.0, args.check_every))
except KeyboardInterrupt:
    print()
    print("COMPANYOS_RUNTIME_WATCHDOG: STOPPED_BY_USER")
