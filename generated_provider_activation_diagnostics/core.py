"""Core implementation for provider_activation_diagnostics.

This module provides a single public function, ``diagnose_provider_activation``,
that inspects provider health/configuration data and returns a structured
diagnostic report. It performs no network access, no financial actions, and no
external actions. It safely handles empty and malformed inputs.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_dict(value: Any) -> bool:
    return isinstance(value, dict)


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "on"}
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip()
    try:
        return str(value)
    except Exception:
        return default


def _diagnose_provider(name: str, provider_data: Any) -> dict[str, Any]:
    """Build a diagnostic entry for a single provider entry.

    Handles malformed/missing fields gracefully.
    """
    if not _is_dict(provider_data):
        return {
            "provider": _safe_str(name),
            "valid": False,
            "configured": False,
            "usable": False,
            "reachable": False,
            "issues": ["malformed_provider_entry"],
            "recommendations": ["malformed_provider_entry"],
        }

    issues: list[str] = []
    recommendations: list[str] = []

    configured = _safe_bool(provider_data.get("configured"), False)
    usable = _safe_bool(provider_data.get("usable"), False)
    reachable = _safe_bool(provider_data.get("reachable"), False)
    provider_name = _safe_str(provider_data.get("provider"), _safe_str(name))

    if not configured:
        issues.append("not_configured")
        recommendations.append("not_configured")
        recommendations.append(
            f"Configure credentials/settings for provider '{provider_name}'."
        )

    if configured and not usable:
        issues.append("configured_but_not_usable")
        recommendations.append("configured_but_not_usable")
        recommendations.append(
            f"Provider '{provider_name}' is configured but marked unusable; "
            "review quota, auth, or health status."
        )

    if configured and not reachable and "reachable" in provider_data:
        issues.append("not_reachable")
        recommendations.append("not_reachable")
        recommendations.append(
            f"Provider '{provider_name}' is not reachable; verify endpoint "
            "availability during actual requests."
        )

    valid = configured and usable

    return {
        "provider": provider_name,
        "valid": valid,
        "configured": configured,
        "usable": usable,
        "reachable": reachable if "reachable" in provider_data else None,
        "issues": issues,
        "recommendations": recommendations,
    }


def diagnose_provider_activation(
    provider_report: Any = None,
    *,
    routing_policy: Any = None,
) -> dict[str, Any]:
    """Diagnose provider activation state from a provider health report.

    Parameters
    ----------
    provider_report:
        Optional dict-like provider health report. Expected to contain
        ``primary`` and/or ``fallback`` provider entries, plus optional
        ``healthy`` and ``routing_policy`` fields. Any shape is accepted;
        malformed inputs are reported safely.
    routing_policy:
        Optional override for the routing policy string.

    Returns
    -------
    dict
        Structured diagnostic report with keys:
        - ``generated_at``: ISO timestamp
        - ``success``: bool, always True (diagnostics ran)
        - ``status``: "provider_activation_diagnostics_complete"
        - ``providers``: list of per-provider diagnostic dicts
        - ``healthy``: bool, True if at least one provider is valid
        - ``primary_active``: bool
        - ``fallback_active``: bool
        - ``issue_count``: int
        - ``recommendations``: list[str]
        - ``routing_policy``: str
        - ``external_actions_taken``: False
    """
    report: dict[str, Any] = {
        "generated_at": _now(),
        "success": True,
        "status": "provider_activation_diagnostics_complete",
        "providers": [],
        "healthy": False,
        "primary_active": False,
        "fallback_active": False,
        "issue_count": 0,
        "recommendations": [],
        "routing_policy": "",
        "external_actions_taken": False,
    }

    if provider_report is None:
        report["providers"] = []
        report["recommendations"] = [
            "No provider report supplied; cannot evaluate activation state."
        ]
        report["issue_count"] = 1
        report["routing_policy"] = _safe_str(routing_policy)
        return report

    if not _is_dict(provider_report):
        report["providers"] = []
        report["recommendations"] = [
            "Provider report is malformed; expected a JSON object."
        ]
        report["issue_count"] = 1
        report["routing_policy"] = _safe_str(routing_policy)
        return report

    providers: list[dict[str, Any]] = []
    all_issues: list[str] = []
    all_recommendations: list[str] = []

    primary_entry = provider_report.get("primary")
    fallback_entry = provider_report.get("fallback")

    if primary_entry is not None:
        primary_diag = _diagnose_provider("primary", primary_entry)
        providers.append(primary_diag)
        all_issues.extend(primary_diag["issues"])
        all_recommendations.extend(primary_diag["recommendations"])
        report["primary_active"] = primary_diag["valid"]
    else:
        all_issues.append("missing_primary_provider")
        all_recommendations.append("missing_primary_provider")
        all_recommendations.append(
            "No primary provider entry found in the report."
        )

    if fallback_entry is not None:
        fallback_diag = _diagnose_provider("fallback", fallback_entry)
        providers.append(fallback_diag)
        all_issues.extend(fallback_diag["issues"])
        all_recommendations.extend(fallback_diag["recommendations"])
        report["fallback_active"] = fallback_diag["valid"]
    else:
        all_issues.append("missing_fallback_provider")
        all_recommendations.append("missing_fallback_provider")
        all_recommendations.append(
            "No fallback provider entry found in the report."
        )

    # If the report itself declares a healthy flag, incorporate it but do not
    # override the computed per-provider validity.
    declared_healthy = _safe_bool(provider_report.get("healthy"), None)
    computed_healthy = any(p["valid"] for p in providers)
    report["healthy"] = bool(computed_healthy)
    if declared_healthy is True and not computed_healthy:
        all_issues.append("declared_healthy_but_no_valid_provider")
        all_recommendations.append("declared_healthy_but_no_valid_provider")
        all_recommendations.append(
            "Report declares healthy but no provider is both configured and usable."
        )

    policy = _safe_str(routing_policy)
    if not policy:
        policy = _safe_str(provider_report.get("routing_policy"))
    report["routing_policy"] = policy

    if not policy:
        all_issues.append("missing_routing_policy")
        all_recommendations.append("missing_routing_policy")
        all_recommendations.append(
            "No routing policy specified; define primary/fallback routing."
        )

    report["providers"] = providers
    report["issue_count"] = len(all_issues)
    report["recommendations"] = all_recommendations

    return report
