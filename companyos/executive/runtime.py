import argparse
import json
import os
import signal
import time
from pathlib import Path
from typing import List

from .engine import ExecutiveEngine
from .models import Venture, Worker


RUNNING = True


def _stop(_signum, _frame):
    global RUNNING
    RUNNING = False


def _runtime_dir() -> Path:
    return Path.home() / "companyos" / "companyos_runtime" / "phase18201_18300"


def _load_inputs(runtime_dir: Path):
    venture_file = runtime_dir / "ventures.json"
    worker_file = runtime_dir / "workers.json"
    finance_file = runtime_dir / "finance_state.json"

    if not venture_file.exists():
        venture_file.write_text(json.dumps(_sample_ventures(), indent=2))
    if not worker_file.exists():
        worker_file.write_text(json.dumps(_sample_workers(), indent=2))
    if not finance_file.exists():
        finance_file.write_text(json.dumps({"available_capital": 0.0}, indent=2))

    ventures = [Venture(**item) for item in json.loads(venture_file.read_text())]
    workers = [Worker(**item) for item in json.loads(worker_file.read_text())]
    finance = json.loads(finance_file.read_text())
    return ventures, workers, float(finance.get("available_capital", 0.0))


def run_once() -> dict:
    runtime_dir = _runtime_dir()
    runtime_dir.mkdir(parents=True, exist_ok=True)
    ventures, workers, capital = _load_inputs(runtime_dir)
    return ExecutiveEngine(runtime_dir).run_cycle(ventures, workers, capital)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=int, default=int(os.environ.get("COMPANYOS_EXECUTIVE_INTERVAL", "60")))
    args = parser.parse_args()

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    if args.once:
        result = run_once()
        print(json.dumps(result, indent=2))
        return

    while RUNNING:
        try:
            result = run_once()
            print(json.dumps({
                "timestamp": result["timestamp"],
                "phase": result["phase"],
                "audit_passed": result["audit"]["passed"],
                "ventures": len(result["ranking"]),
            }), flush=True)
        except Exception as exc:
            print(json.dumps({"runtime_error": str(exc)}), flush=True)
        for _ in range(max(1, args.interval)):
            if not RUNNING:
                break
            time.sleep(1)


def _sample_ventures() -> List[dict]:
    return [
        {
            "venture_id": "sample-venture-1",
            "name": "Sample Venture",
            "stage": "validation",
            "expected_return": 0.5,
            "confidence": 0.5,
            "risk": 0.4,
            "urgency": 0.5,
            "strategic_fit": 0.6,
            "capital_requested": 0.0,
            "workers_requested": 1,
            "progress": 0.2,
            "failure_probability": 0.2,
            "dependencies": [],
            "blocked": False,
            "metrics": {"demand": 0.4, "margin": 0.4, "retention": 0.3},
        }
    ]


def _sample_workers() -> List[dict]:
    return [
        {
            "worker_id": "generalist-1",
            "specialty": "general",
            "capacity": 1.0,
            "current_load": 0.0,
            "reliability": 0.8,
        }
    ]


if __name__ == "__main__":
    main()
