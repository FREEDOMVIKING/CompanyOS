import argparse
import json
import os
import signal
import time

from .engine import OperationsEngine

RUNNING = True

def stop(_sig, _frame):
    global RUNNING
    RUNNING = False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=int, default=int(os.environ.get("COMPANYOS_OPSCENTER_INTERVAL", "30")))
    args = parser.parse_args()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    engine = OperationsEngine()

    if args.once:
        print(json.dumps(engine.run_cycle(), indent=2))
        return

    while RUNNING:
        try:
            result = engine.run_cycle()
            print(json.dumps({
                "timestamp": result["generated_at"],
                "phase": result["phase"],
                "ventures": result["kpis"]["venture_count"],
                "task_assignment_rate": result["kpis"]["task_assignment_rate"],
                "bottlenecks": len(result["bottlenecks"]),
            }), flush=True)
        except Exception as exc:
            print(json.dumps({"opscenter_error": str(exc)}), flush=True)
        for _ in range(max(1, args.interval)):
            if not RUNNING:
                break
            time.sleep(1)

if __name__ == "__main__":
    main()
