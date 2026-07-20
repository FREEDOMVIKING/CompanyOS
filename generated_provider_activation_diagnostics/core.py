#!/usr/bin/env python3
"""Core implementation for provider activation diagnostics.

This module inspects provider configuration data and produces structured
diagnostics about activation readiness. It performs NO network access, NO
financial actions, and NO external actions. It only validates in-memory data.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

REQUIRED_PROVIDER_FIELDS = ("provider", "status")

VALID_STATUSES = (
    "active",
    "inactive",
    "configured",
    "unconfigured",
    "error",
    "unknown",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_dict(value: Any) -> bool:
    return isinstance(value, dict)


def _coerce_providers(providers: Any) -> list[dict[str, Any]]:
    """Normalize the providers input into a list of dicts.

    Malformed entries are replaced with sentinel dicts so diagnostics can
    report them rather than crash.
    """
    if providers is None:
        return []
    if isinstance(providers, dict):
        # Treat a single provider dict as a one-element list.
        return [providers]
    if isinstance(providers, list):
        result: list[dict[str, Any]] = []
        for entry in providers:
            if _is_dict(entry):
                result.append(entry)
            else:
                result.append({"provider": None, "status": None, "_malformed": True})
        return result
    # Unknown shape: return empty rather than raising.
    return []


def _diagnose_single(provider: dict[str, Any], index: int) -> dict[str, Any]:
    """Produce a diagnostic record for a single provider entry."""
    issues: list[str] = []
    warnings: list[str] = []

    if provider.get("_malformed"):
        return {
            "index": index,
            "provider": None,
            "status": "unknown",
            "configured": False,
            "has_credentials": False,
            "reachable": False,
            "activated": False,
            "ready": False,
            "issues": ["malformed_provider_entry"],
            "warnings": [],
            "missing_fields": list(REQUIRED_PROVIDER_FIELDS),
        }

    name = provider.get("provider")
    status = provider.get("status")

    missing_fields = [
        field for field in REQUIRED_PROVIDER_FIELDS if field not in provider
    ]

    if not isinstance(name, str) or not name.strip():
        issues.append("missing_or_invalid_provider_name")
        name = None

    if not isinstance(status, str) or not status.strip():
        issues.append("missing_or_invalid_status")
        status = "unknown"
    elif status not in VALID_STATUSES:
        warnings.append(f"unrecognized_status:{status}")

    configured = bool(provider.get("configured", False))
    has_credentials = bool(provider.get("has_credentials", False))
    reachable = bool(provider.get("reachable", False))

    if status == "active" and not configured:
        warnings.append("active_without_configured_flag")
    if status == "active" and not has_credentials:
        issues.append("active_without_credentials")
    if status == "active" and not reachable:
        warnings.append("active_without_reachable_flag")

    activated = status == "active" and configured and has_credentials
    ready = activated and reachable

    return {
        "index": index,
        "provider": name,
        "status": status,
        "configured": configured,
        "has_credentials": has_credentials,
        "reachable": reachable,
        "activated": activated,
        "ready": ready,
        "issues": issues,
        "warnings": warnings,
        "missing_fields": missing_fields,
    }


def diagnose_provider_activation(
    providers: Any = None,
    *,
    require_credentials: bool = True,
    require_reachable: bool = False,
) -> dict[str, Any]:
    """Diagnose provider activation readiness from in-memory configuration.

    Parameters
    ----------
    providers:
        A single provider dict, a list of provider dicts, or None. Each provider
        dict may contain ``provider``, ``status``, ``configured``,
        ``has_credentials``, and ``reachable`` fields. Malformed entries are
        reported safely rather than raising.
    require_credentials:
        When True, a provider cannot be considered activated without
        ``has_credentials`` truthy.
    require_reachable:
        When True, a provider cannot be considered ready unless ``reachable``
        is truthy.

    Returns
    -------
    dict
        Structured diagnostic report with per-provider details and summary
        counts. Always returns a dict; never raises on bad input.
    """
    normalized = _coerce_providers(providers)

    diagnostics: list[dict[str, Any]] = []
    for index, provider in enumerate(normalized):
        diag = _diagnose_single(provider, index)

        # Re-evaluate activated/ready using caller overrides.
        status = diag.get("status")
        configured = diag.get("configured", False)
        has_credentials = diag.get("has_credentials", False)
        reachable = diag.get("reachable", False)

        activated = status == "active" and configured
        if require_credentials and not has_credentials:
            activated = False

        ready = activated
        if require_reachable and not reachable:
            ready = False

        diag["activated"] = activated
        diag["ready"] = ready
        diagnostics.append(diag)

    total = len(diagnostics)
    activated_count = sum(1 for d in diagnostics if d.get("activated"))
    ready_count = sum(1 for d in diagnostics if d.get("ready"))
    issue_count = sum(len(d.get("issues", [])) for d in diagnostics)
    warning_count = sum(len(d.get("warnings", [])) for d in diagnostics)

    providers_with_issues = [
        {"index": d["index"], "provider": d.get("provider"), "issues": d.get("issues", [])}
        for d in diagnostics
        if d.get("issues")
    ]

    # Healthy requires at least one provider and no blocking issues with at
    # least one activated provider.
    healthy = total > 0 and issue_count == 0 and activated_count > 0

    return {
        "generated_at": _now(),
        "capability": "provider_activation_diagnostics",
        "total_providers": total,
        "activated_count": activated_count,
        "ready_count": ready_count,
        "issue_count": issue_count,
        "warning_count": warning_count,
        "healthy": healthy,
        "require_credentials": require_credentials,
        "require_reachable": require_reachable,
        "diagnostics": diagnostics,
        "providers_with_issues": providers_with_issues,
        "external_actions_performed": False,
        "network_access_performed": False,
    }
