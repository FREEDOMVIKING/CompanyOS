from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from companyos.walletintegration.runtime_service_manager import RuntimeServiceManager
from companyos.runtime.ceo_runtime_control_plane import CEORuntimeControlPlane


@dataclass(frozen=True)
class UnifiedRuntimeStatus:
    financial_runtime_ready: bool
    financial_reason: str
    financial_supervisor_running: bool
    financial_watchdog_running: bool
    ceo_runtime_running: bool
    ceo_runtime_ready: bool
    ceo_runtime_reason: str
    ceo_cycle_count: int
    active_orchestrations: int
    completed_orchestrations: int
    failed_orchestrations: int
    halted_orchestrations: int
    unified_ready: bool
    reason: str


class UnifiedRuntimeStackManager:
    """
    Combines:
    - Phase 92 financial/runtime supervisor + watchdog stack
    - Phase 101 autonomous CEO runtime service

    Into one control surface.

    The manager itself does not sign/broadcast transactions and does not
    perform external actions.
    """

    def __init__(self) -> None:
        self.financial = RuntimeServiceManager()
        self.ceo = CEORuntimeControlPlane()

    def status(self) -> UnifiedRuntimeStatus:
        fin = self.financial.status()
        ceo = self.ceo.status()

        ready = bool(fin.service_ready and ceo.running and ceo.ready)

        if ready:
            reason = "unified_runtime_healthy"
        elif not fin.service_ready:
            reason = f"financial_stack_not_ready:{fin.reason}"
        elif not ceo.running:
            reason = "ceo_runtime_not_running"
        elif not ceo.ready:
            reason = f"ceo_runtime_not_ready:{ceo.reason}"
        else:
            reason = "unified_runtime_not_ready"

        return UnifiedRuntimeStatus(
            financial_runtime_ready=fin.service_ready,
            financial_reason=fin.reason,
            financial_supervisor_running=fin.supervisor_running,
            financial_watchdog_running=fin.watchdog_running,
            ceo_runtime_running=ceo.running,
            ceo_runtime_ready=ceo.ready,
            ceo_runtime_reason=ceo.reason,
            ceo_cycle_count=ceo.cycle_count,
            active_orchestrations=ceo.active_orchestrations,
            completed_orchestrations=ceo.completed_orchestrations,
            failed_orchestrations=ceo.failed_orchestrations,
            halted_orchestrations=ceo.halted_orchestrations,
            unified_ready=ready,
            reason=reason,
        )

    def start(
        self,
        *,
        financial_supervisor_interval: float = 15.0,
        watchdog_check_every: float = 30.0,
        financial_max_failures: int = 5,
        restart_backoff: float = 5.0,
        ceo_interval: float = 10.0,
        ceo_max_failures: int = 5,
    ) -> UnifiedRuntimeStatus:
        fin = self.financial.start(
            supervisor_interval=financial_supervisor_interval,
            watchdog_check_every=watchdog_check_every,
            max_failures=financial_max_failures,
            restart_backoff=restart_backoff,
        )

        if not fin.service_ready:
            return self.status()

        self.ceo.start(
            interval_seconds=ceo_interval,
            max_failures=ceo_max_failures,
        )

        return self.status()

    def stop(self) -> UnifiedRuntimeStatus:
        self.ceo.stop()
        self.financial.stop()
        return self.status()
