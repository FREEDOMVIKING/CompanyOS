from __future__ import annotations

from typing import Any

from companyos.runtime.ceo_scheduler_financial_integration import (
    run_scheduler_financial_cycle,
)


def execute_ceo_financial_scheduler_hook(
    context: dict[str, Any] | None = None,
):
    context = dict(context or {})

    cycle_id = str(
        context.get("cycle_id")
        or context.get("run_id")
        or context.get("scheduler_cycle_id")
        or ""
    )

    return run_scheduler_financial_cycle(
        cycle_id=cycle_id,
        financial_intent=context.get("financial_intent"),
        metadata=context,
    )
