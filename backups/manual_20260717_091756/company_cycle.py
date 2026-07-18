#!/usr/bin/env python3

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
MEMORY_DIR = BASE_DIR / "ceo_memory"

STATE_FILE = MEMORY_DIR / "company_state.json"
TASKS_FILE = MEMORY_DIR / "tasks.json"
RESULTS_FILE = MEMORY_DIR / "agent_results.json"
CYCLE_LOG_FILE = MEMORY_DIR / "company_cycles.json"

COMPANY_MANAGER = BASE_DIR / "company_manager.py"

MAX_MANAGER_RUNS_PER_CYCLE = 10
DEFAULT_LOOP_DELAY_SECONDS = 300


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary = path.with_suffix(path.suffix + ".tmp")

    with temporary.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    temporary.replace(path)


def run_command(command: list[str], timeout: int = 120) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "return_code": None,
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
        }

    except Exception as error:
        return {
            "success": False,
            "return_code": None,
            "stdout": "",
            "stderr": str(error),
        }


def get_task_status(task: dict[str, Any]) -> str:
    return str(task.get("status", "unknown")).lower()


def count_tasks() -> dict[str, int]:
    tasks = load_json(TASKS_FILE, [])

    counts = {
        "total": len(tasks),
        "pending": 0,
        "running": 0,
        "completed": 0,
        "failed": 0,
        "other": 0,
    }

    for task in tasks:
        status = get_task_status(task)

        if status in counts:
            counts[status] += 1
        elif status in {"queued", "waiting"}:
            counts["pending"] += 1
        elif status in {"done", "successful", "success"}:
            counts["completed"] += 1
        elif status in {"error", "rejected"}:
            counts["failed"] += 1
        else:
            counts["other"] += 1

    return counts


def count_results() -> int:
    results = load_json(RESULTS_FILE, [])

    if isinstance(results, list):
        return len(results)

    if isinstance(results, dict):
        return len(results)

    return 0


def run_ceo_decision() -> dict[str, Any]:
    if not COMPANY_MANAGER.exists():
        return {
            "success": False,
            "stderr": "company_manager.py was not found",
            "stdout": "",
        }

    return run_command(
        [sys.executable, str(COMPANY_MANAGER)],
        timeout=120,
    )



def run_scoring_cycle() -> dict[str, Any]:
    return run_command(
        [sys.executable, "-m", "agents.scoring_agent"],
        timeout=180,
    )


def run_learning_cycle() -> dict[str, Any]:
    return run_command(
        [sys.executable, "-m", "agents.learning_agent"],
        timeout=180,
    )


def run_executive_review() -> dict[str, Any]:
    return run_command(
        [sys.executable, "-m", "agents.executive_agent"],
        timeout=120,
    )


def run_recovery_scan() -> dict[str, Any]:
    return run_command(
        [sys.executable, "-m", "agents.recovery_agent"],
        timeout=120,
    )



def dispatch_tasks() -> list[dict[str, Any]]:
    dispatch_reports = []

    for attempt in range(1, MAX_MANAGER_RUNS_PER_CYCLE + 1):
        before = count_tasks()

        if before["pending"] <= 0:
            break

        result = run_command(
            [sys.executable, "-m", "agents.manager"],
            timeout=180,
        )

        after = count_tasks()

        dispatch_reports.append({
            "attempt": attempt,
            "before": before,
            "after": after,
            "manager_result": result,
        })

        if not result["success"]:
            break

        if after["pending"] >= before["pending"]:
            break

    return dispatch_reports


def create_cycle_report() -> dict[str, Any]:
    cycle_started = now()
    tasks_before = count_tasks()
    results_before = count_results()

    print("=" * 60)
    print("AUTONOMOUS COMPANY CYCLE")
    print("Started:", cycle_started)
    print("=" * 60)

    print("\n[1/3] CEO is reviewing the company...")
    ceo_result = run_ceo_decision()

    if ceo_result["stdout"]:
        print(ceo_result["stdout"])

    if ceo_result["stderr"]:
        print("CEO ERROR:", ceo_result["stderr"])

    print("\n[2/5] Executives are reviewing departments...")
    executive_result = run_executive_review()

    if executive_result["stdout"]:
        print(executive_result["stdout"])

    if executive_result["stderr"]:
        print("EXECUTIVE ERROR:", executive_result["stderr"])

    print("\n[3/5] Checking failed tasks...")
    recovery_result = run_recovery_scan()

    if recovery_result["stdout"]:
        print(recovery_result["stdout"])

    if recovery_result["stderr"]:
        print("RECOVERY ERROR:", recovery_result["stderr"])

    print("\n[4/5] Dispatching worker tasks...")
    dispatch_reports = dispatch_tasks()

    if not dispatch_reports:
        print("No pending worker tasks.")

    for report in dispatch_reports:
        manager_result = report["manager_result"]

        print(
            f"Dispatch attempt {report['attempt']}: "
            f"{report['before']['pending']} pending -> "
            f"{report['after']['pending']} pending"
        )

        if manager_result["stdout"]:
            print(manager_result["stdout"])

        if manager_result["stderr"]:
            print("MANAGER ERROR:", manager_result["stderr"])

    print("\n[5/7] Scoring business opportunities...")
    scoring_result = run_scoring_cycle()

    if scoring_result["stdout"]:
        print(scoring_result["stdout"])

    if scoring_result["stderr"]:
        print("SCORING ERROR:", scoring_result["stderr"])

    print("\n[6/7] Learning from company activity...")
    learning_result = run_learning_cycle()

    if learning_result["stdout"]:
        print(learning_result["stdout"])

    if learning_result["stderr"]:
        print("LEARNING ERROR:", learning_result["stderr"])

    print("\n[7/7] Saving company report...")

    tasks_after = count_tasks()
    results_after = count_results()
    state = load_json(STATE_FILE, {})

    report = {
        "cycle_started_at": cycle_started,
        "cycle_finished_at": now(),
        "success": (
            ceo_result["success"]
            and executive_result["success"]
            and recovery_result["success"]
            and learning_result["success"]
            and scoring_result["success"]
            and all(
                item["manager_result"]["success"]
                for item in dispatch_reports
            )
        ),
        "ceo_result": ceo_result,
        "executive_result": executive_result,
        "learning_result": learning_result,
        "scoring_result": scoring_result,
        "recovery_result": recovery_result,
        "dispatch_attempts": len(dispatch_reports),
        "tasks_before": tasks_before,
        "tasks_after": tasks_after,
        "results_before": results_before,
        "results_after": results_after,
        "company_state": state,
    }

    cycle_logs = load_json(CYCLE_LOG_FILE, [])

    if not isinstance(cycle_logs, list):
        cycle_logs = []

    cycle_logs.append(report)

    # Keep only the most recent 100 cycle reports.
    cycle_logs = cycle_logs[-100:]

    save_json(CYCLE_LOG_FILE, cycle_logs)

    print("Cycle success:", report["success"])
    print("Pending tasks:", tasks_after["pending"])
    print("Completed tasks:", tasks_after["completed"])
    print("Failed tasks:", tasks_after["failed"])
    print("Total stored results:", results_after)
    print("=" * 60)

    return report


def run_loop(delay_seconds: int) -> None:
    print(
        "Company loop started. "
        f"A new cycle will run every {delay_seconds} seconds."
    )
    print("Press Ctrl+C to stop safely.")

    try:
        while True:
            create_cycle_report()
            print(f"\nSleeping for {delay_seconds} seconds...\n")
            time.sleep(delay_seconds)

    except KeyboardInterrupt:
        print("\nCompany loop stopped safely.")


def main() -> None:
    args = sys.argv[1:]

    if "--loop" in args:
        delay = DEFAULT_LOOP_DELAY_SECONDS

        if "--delay" in args:
            index = args.index("--delay")

            try:
                delay = int(args[index + 1])
            except (IndexError, ValueError):
                print("--delay must be followed by a number of seconds")
                raise SystemExit(1)

        if delay < 30:
            print("Minimum loop delay is 30 seconds")
            raise SystemExit(1)

        run_loop(delay)
        return

    report = create_cycle_report()

    if not report["success"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
