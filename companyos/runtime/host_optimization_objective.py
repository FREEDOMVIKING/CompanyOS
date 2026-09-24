from __future__ import annotations

import json
import time
from pathlib import Path

RT = Path.home() / ".companyos_runtime"


def load(path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def build_objective():
    supervisor = load(
        RT / "service_supervisor_state.json",
        {}
    )

    migration = load(
        RT / "authorized_local_migration_state.json",
        {}
    )

    services = supervisor.get("services") or {}

    down = []
    failures = 0
    restarts = 0

    for name, row in services.items():
        if not row.get("running"):
            down.append(name)

        failures += int(
            row.get("consecutive_failures") or 0
        )

        restarts += int(
            row.get("restarts") or 0
        )

    focus = []

    if down or failures:
        focus.append(
            "reduce runtime failures and improve recovery"
        )

    if restarts:
        focus.append(
            "reduce unnecessary service restarts"
        )

    if migration.get("best_candidate"):
        focus.append(
            "improve host scoring and migration reliability"
        )

    focus.extend([
        "increase useful task throughput",
        "reduce CPU and memory waste",
        "improve distributed worker scheduling",
        "improve state synchronization",
        "improve authorized-host capacity pooling",
        "improve failover and recovery",
    ])

    goal = (
        "Autonomously optimize CompanyOS host and compute "
        "performance. "
        + "; ".join(focus)
        + ". Prefer measurable improvements. "
          "Modify only authorized host/runtime modules and tests. "
          "Every candidate must compile and pass validation. "
          "Preserve authorized-host-only access and existing "
          "security, finance, credential, approval, and "
          "self-evolution protections."
    )

    return {
        "schema":
            "companyos.host_optimization.v69_35i",

        "generated_at_unix":
            time.time(),

        "service_failures":
            failures,

        "service_restarts":
            restarts,

        "services_down":
            down,

        "recommended_goal":
            goal,
    }


if __name__ == "__main__":
    print(
        json.dumps(
            build_objective(),
            indent=2,
            sort_keys=True
        )
    )
