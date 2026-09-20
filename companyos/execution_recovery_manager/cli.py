"""Runtime diagnostics for adaptive execution services.

This module is intentionally observational: it reports process availability and
never starts, stops, or mutates a service.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from typing import Iterable


SERVICE_NAMES = (
    "adaptive_worker_factory",
    "adaptive_workforce_execution_bridge",
    "autonomous_diagnostics",
    "autonomous_evidence_acquisition",
    "capability_expansion",
    "capability_feedback",
    "capability_request_executor",
    "closed_loop_outcome_evaluator",
)


@dataclass(frozen=True)
class ServiceObservation:
    service: str
    running: bool
    matching_pids: tuple[int, ...]
    evidence: str


def _process_rows() -> Iterable[tuple[int, str]]:
    """Yield process ids and command lines without failing the whole probe."""
    try:
        result = subprocess.run(
            ["ps", "-eo", "pid=,args="],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return
    for line in result.stdout.splitlines():
        fields = line.strip().split(maxsplit=1)
        if len(fields) != 2:
            continue
        try:
            yield int(fields[0]), fields[1]
        except ValueError:
            continue


def _matches(service: str, command: str) -> bool:
    command = command.lower()
    name = service.lower()
    tokens = command.replace("/", " ").replace("-", "_").split()
    return any(name == token or name in token for token in tokens)


def observe_services(names: Iterable[str] = SERVICE_NAMES) -> list[ServiceObservation]:
    rows = tuple(_process_rows())
    observations: list[ServiceObservation] = []
    for service in names:
        pids = tuple(pid for pid, command in rows if _matches(service, command))
        observations.append(
            ServiceObservation(
                service=service,
                running=bool(pids),
                matching_pids=pids,
                evidence=(
                    f"matched process ids: {', '.join(map(str, pids))}"
                    if pids
                    else "no matching process was observed"
                ),
            )
        )
    return observations


def diagnostic_report() -> dict[str, object]:
    observations = observe_services()
    missing = [item.service for item in observations if not item.running]
    return {
        "source": "execution_recovery_manager",
        "host": os.uname().nodename if hasattr(os, "uname") else "unknown",
        "services": [asdict(item) for item in observations],
        "running_count": len(observations) - len(missing),
        "missing_count": len(missing),
        "missing_services": missing,
        "recommended_next_step": (
            "inspect service logs and supervisor state for missing services"
            if missing
            else "continue normal runtime observation"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="return failure when a service is absent")
    args = parser.parse_args(argv)
    report = diagnostic_report()
    print(json.dumps(report, sort_keys=True))
    return 1 if args.strict and report["missing_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
