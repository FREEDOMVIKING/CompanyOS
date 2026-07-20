"""Core implementation for provider activation diagnostics.

The public entry point is :func:`diagnose_provider_activation`, which accepts
structured provider activation records and returns a structured diagnostic
report. The function is pure: it does not touch the network, the filesystem,
or any external system.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence


class ProviderActivationDiagnosticsError(ValueError):
    """Raised when inputs cannot be processed safely."""


_REQUIRED_PROVIDER_FIELDS = ("provider",)

_VALID_ACTIVATION_STATES = {
    "active",
    "inactive",
    "degraded",
    "pending",
    "failed",
    "unknown",
}

_VALID_ROLES = {
    "primary",
    "fallback",
    "secondary",
    "standby",
    "unknown",
}


def _is_mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def _is_string(value: Any) -> bool:
    return isinstance(value, str)


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def _coerce_records(providers: Any) -> List[Dict[str, Any]]:
    """Normalize the accepted input shapes into a list of record dicts.

    Accepted shapes:
      * None / empty -> []
      * list/tuple of provider mappings
      * mapping with a "providers" list
      * mapping of provider_name -> provider mapping
    """
    if providers is None:
        return []

    if isinstance(providers, str):
        raise ProviderActivationDiagnosticsError(
            "providers must be a list or mapping, not a string"
        )

    if isinstance(providers, (list, tuple)):
        records: List[Dict[str, Any]] = []
        for index, item in enumerate(providers):
            if not _is_mapping(item):
                raise ProviderActivationDiagnosticsError(
                    f"provider entry at index {index} must be a mapping"
                )
            records.append(dict(item))
        return records

    if _is_mapping(providers):
        if "providers" in providers:
            nested = providers.get("providers")
            if nested is None:
                return []
            if not isinstance(nested, (list, tuple)):
                raise ProviderActivationDiagnosticsError(
                    "'providers' field must be a list"
                )
            return _coerce_records(list(nested))

        # Treat as name -> record mapping.
        records = []
        for name, value in providers.items():
            if not _is_string(name):
                raise ProviderActivationDiagnosticsError(
                    "provider mapping keys must be strings"
                )
            if not _is_mapping(value):
                raise ProviderActivationDiagnosticsError(
                    f"provider '{name}' must be a mapping"
                )
            record = dict(value)
            record.setdefault("provider", name)
            records.append(record)
        return records

    raise ProviderActivationDiagnosticsError(
        "providers must be a list, mapping, or None"
    )


def _safe_get_str(record: Mapping[str, Any], key: str) -> Optional[str]:
    value = record.get(key)
    if value is None:
        return None
    if not _is_string(value):
        return None
    return value


def _safe_get_bool(record: Mapping[str, Any], key: str) -> Optional[bool]:
    value = record.get(key)
    if value is None:
        return None
    if not _is_bool(value):
        return None
    return value


def _normalize_state(state: Optional[str]) -> str:
    if state is None:
        return "unknown"
    lowered = state.strip().lower()
    if lowered not in _VALID_ACTIVATION_STATES:
        return "unknown"
    return lowered


def _normalize_role(role: Optional[str]) -> str:
    if role is None:
        return "unknown"
    lowered = role.strip().lower()
    if lowered not in _VALID_ROLES:
        return "unknown"
    return lowered


def _diagnose_record(record: Mapping[str, Any]) -> Dict[str, Any]:
    provider = _safe_get_str(record, "provider")
    if not provider:
        provider = "unnamed_provider"

    state = _normalize_state(_safe_get_str(record, "activation_state") or _safe_get_str(record, "state"))
    role = _normalize_role(_safe_get_str(record, "role"))

    configured = _safe_get_bool(record, "configured")
    usable = _safe_get_bool(record, "usable")
    reachable = _safe_get_bool(record, "reachable")
    healthy = _safe_get_bool(record, "healthy")

    issues: List[str] = []

    if configured is False:
        issues.append("provider_not_configured")
    if usable is False:
        issues.append("provider_not_usable")
    if reachable is False:
        issues.append("provider_not_reachable")
    if healthy is False:
        issues.append("provider_unhealthy")

    if state == "failed":
        issues.append("activation_failed")
    elif state == "degraded":
        issues.append("activation_degraded")
    elif state == "pending":
        issues.append("activation_pending")
    elif state == "inactive":
        issues.append("activation_inactive")
    elif state == "unknown":
        issues.append("activation_state_unknown")

    # Activation readiness heuristic (purely internal, no external checks).
    ready = (
        state == "active"
        and configured is not False
        and usable is not False
        and reachable is not False
        and healthy is not False
    )

    severity = "ok"
    if state == "failed" or healthy is False:
        severity = "high"
    elif state in {"degraded", "pending"} or reachable is False or usable is False:
        severity = "medium"
    elif issues:
        severity = "low"

    return {
        "provider": provider,
        "role": role,
        "activation_state": state,
        "configured": configured,
        "usable": usable,
        "reachable": reachable,
        "healthy": healthy,
        "activation_ready": ready,
        "severity": severity,
        "issues": issues,
    }


def _build_summary(
    diagnostics: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    total = len(diagnostics)
    ready = sum(1 for d in diagnostics if d.get("activation_ready"))
    failed = sum(1 for d in diagnostics if d.get("activation_state") == "failed")
    degraded = sum(1 for d in diagnostics if d.get("activation_state") == "degraded")
    pending = sum(1 for d in diagnostics if d.get("activation_state") == "pending")
    inactive = sum(1 for d in diagnostics if d.get("activation_state") == "inactive")
    active = sum(1 for d in diagnostics if d.get("activation_state") == "active")
    unknown = sum(1 for d in diagnostics if d.get("activation_state") == "unknown")

    high = sum(1 for d in diagnostics if d.get("severity") == "high")
    medium = sum(1 for d in diagnostics if d.get("severity") == "medium")
    low = sum(1 for d in diagnostics if d.get("severity") == "low")

    primary_ready = any(
        d.get("activation_ready") and d.get("role") == "primary"
        for d in diagnostics
    )
    fallback_ready = any(
        d.get("activation_ready") and d.get("role") == "fallback"
        for d in diagnostics
    )

    recommendations: List[str] = []
    if total == 0:
        recommendations.append("No provider activation records supplied.")
    else:
        if not primary_ready:
            recommendations.append(
                "No primary provider is activation-ready; review primary configuration."
            )
        if not fallback_ready:
            recommendations.append(
                "No fallback provider is activation-ready; verify fallback resilience."
            )
        if failed:
            recommendations.append(
                f"{failed} provider(s) reported a failed activation; investigate before routing work."
            )
        if degraded:
            recommendations.append(
                f"{degraded} provider(s) are degraded; consider reduced routing volume."
            )
        if pending:
            recommendations.append(
                f"{pending} provider(s) are pending activation; re-check before promotion."
            )
        if unknown:
            recommendations.append(
                f"{unknown} provider(s) have an unknown activation state; supply explicit status."
            )
        if high:
            recommendations.append(
                f"{high} provider(s) have high-severity issues requiring attention."
            )
        if ready == total and total > 0:
            recommendations.append(
                "All supplied providers are activation-ready."
            )

    overall = "healthy"
    if total == 0:
        overall = "empty"
    elif high:
        overall = "critical"
    elif medium or failed or degraded:
        overall = "degraded"
    elif low or pending or unknown:
        overall = "attention"
    elif ready == total:
        overall = "healthy"

    return {
        "total_providers": total,
        "active": active,
        "inactive": inactive,
        "degraded": degraded,
        "pending": pending,
        "failed": failed,
        "unknown": unknown,
        "activation_ready": ready,
        "severity_counts": {
            "high": high,
            "medium": medium,
            "low": low,
            "ok": total - high - medium - low,
        },
        "primary_ready": primary_ready,
        "fallback_ready": fallback_ready,
        "overall_status": overall,
        "recommendations": recommendations,
    }


def diagnose_provider_activation(
    providers: Any = None,
    *,
    include_records: bool = True,
) -> Dict[str, Any]:
    """Return structured diagnostics for provider activation records.

    Parameters
    ----------
    providers:
        Optional provider activation records. May be:
          * ``None`` or empty (returns an empty-state report)
          * a list/tuple of provider mappings
          * a mapping with a ``"providers"`` list
          * a mapping of provider name -> provider mapping

        Each provider mapping may include:
          * ``provider`` (str): provider name
          * ``activation_state`` or ``state`` (str): one of
            active/inactive/degraded/pending/failed/unknown
          * ``role`` (str): primary/fallback/secondary/standby/unknown
          * ``configured`` (bool)
          * ``usable`` (bool)
          * ``reachable`` (bool)
          * ``healthy`` (bool)

    include_records:
        When ``True`` (default), the per-provider diagnostics are included
        in the returned report under ``"providers"``.

    Returns
    -------
    dict
        A structured diagnostic report with keys:
          * ``success`` (bool)
          * "status" (str)
          * "summary" (dict)
          * "providers" (list[dict]) when ``include_records`` is True
          * "external_actions_performed" (bool, always False)
          * "network_access_performed" (bool, always False)

    Raises
    ------
    ProviderActivationDiagnosticsError
        If the input shape is malformed in a way that cannot be safely
        interpreted.
    """
    records = _coerce_records(providers)
    diagnostics = [_diagnose_record(record) for record in records]
    summary = _build_summary(diagnostics)

    report: Dict[str, Any] = {
        "success": True,
        "status": "provider_activation_diagnostics_complete",
        "summary": summary,
        "external_actions_performed": False,
        "network_access_performed": False,
        "financial_actions_performed": False,
    }

    if include_records:
        report["providers"] = diagnostics

    return report


__all__ = [
    "diagnose_provider_activation",
    "ProviderActivationDiagnosticsError",
]
