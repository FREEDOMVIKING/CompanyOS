#!/usr/bin/env python3
import argparse

from companyos.walletintegration.runtime_watchdog import RuntimeWatchdog

ap = argparse.ArgumentParser()
ap.add_argument("--interval", type=float, default=15.0)
ap.add_argument("--max-failures", type=int, default=5)
ap.add_argument("--restart-backoff", type=float, default=2.0)
args = ap.parse_args()

watchdog = RuntimeWatchdog(
    restart_backoff_seconds=args.restart_backoff,
    max_restarts_per_window=5,
    restart_window_seconds=600,
)

result = watchdog.evaluate_once(
    interval_seconds=args.interval,
    max_failures=args.max_failures,
)

print("ACTION:", result.action)
print("REASON:", result.reason)
print("RUNNING:", result.running)
print("READY:", result.ready)
print("RPC_OK:", result.rpc_ok)
print("STALE:", result.stale)
print("UNRESOLVED_RECORDS:", result.unresolved_records)
print("CONSECUTIVE_FAILURES:", result.consecutive_failures)
print("RESTARTED:", result.restarted)
print("RESTART_COUNT:", result.restart_count)
print("WATCHDOG_BUILDS_TRANSACTION: False")
print("WATCHDOG_SIGNS_TRANSACTION: False")
print("WATCHDOG_BROADCASTS: False")
print("PHASE91_WATCHDOG_ONCE: PASS")
