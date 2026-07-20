"""Core implementation for provider activation diagnostics.

The :func:`diagnose_provider_activation` function inspects a structured
description of provider activation records and returns a structured
diagnostic report. It is intentionally pure: no I/O, no network, and no
side effects.
"""

from __future__ import annotations

from typing import Any, Iterable

REQUIRED_FIELDS = ("provider", "configured", "usable")


def _is_truthy(value: Any) -> bool:
    """Return True for values commonly interpreted as enabled/true."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}
    if isinstance(value, (int, float)):
        return value != 0
    return False


def _coerce_providers(providers: Any) -> list[dict[str, Any]]:
    """Normalize the input into a list of provider dictionaries."""
    if providers is None:
        return []

    if isinstance(providers, dict):
        # A single provider dict.
        if "provider" in providers or "configured" in providers:
            return [providers]
        # A mapping of provider names to provider dicts.
        result: list[dict[str, Any]] = []
        for name, value in providers.items():
            if isinstance(value, dict):
                merged = dict(value)
                merged.setdefault("provider", str(name))
                result.append(merged)
            else:
                result.append({"provider": str(name), "configured": value})
        return result

    if isinstance(providers, list):
        result = []
        for item in providers:
            if isinstance(item, dict):
                result.append(item)
            elif isinstance(item, str):
                result.append({"provider": item})
            else:
                result.append({"provider": str(item)})
        return result

    if isinstance(providers, (str, int, float, bool)):
        return [{"provider": str(providers)}]

    return []


def _diagnose_single(provider: dict[str, Any], index: int) -> dict[str, Any]:
    """Build a diagnostic record for a single provider entry."""
    name = provider.get("provider")
    missing_fields = [
        field for field in REQUIRED_FIELDS if field not in provider
    ]

    configured = _is_truthy(provider.get("configured", False))
    usable = _is_truthy(provider.get("usable", False))
    reachable = _is_truthy(provider.get("reachable", False))

    issues: list[str] = []

    if not name:
        issues.append("missing_provider_name")
    if missing_fields:
        issues.append(f"missing_fields:{','.join(missing_fields)}")
    if configured and not usable:
        issues.append("configured_but_not_usable")
    if usable and not configured:
        issues.append("usable_without_configuration")
    if "reachable" in provider and usable and not reachable:
        issues.append("usable_but_not_reachable")

    if configured and usable:
        activation_state = "active"
    elif configured and not usable:
        activation_state = "configured_inactive"
    elif not configured and usable:
        activation_state = "usable_unconfigured"
    else:
        activation_state = "inactive"

    return {
        "index": index,
        "provider": name if name else f"unnamed_{index}",
        "configured": configured,
        "usable": usable,
        "reachable": reachable if "reachable" in provider else None,
        "activation_state": activation_state,
        "missing_fields": missing_fields,
        "issues": issues,
        "valid": len(issues) == 0,
    }


def diagnose_provider_activation(providers: Any = None) -> dict[str, Any]:
    """Diagnose provider activation records.

    Parameters
    ----------
    providers:
        Either a single provider dict, a mapping of provider names to
        provider dicts, a list of provider dicts, or ``None``. Malformed
        inputs are handled safely and reported in the diagnostics.

    Returns
    -------
    dict
        A structured diagnostic report containing:

        - ``provider_count``: number of provider entries analyzed.
        - ``active_count``: number of providers in the ``active`` state.
        - ``inactive_count``: number of providers in the ``inactive`` state.
        - ``configured_inactive_count``: providers configured but not usable.
        - ``usable_unconfigured_count``: providers usable but not configured.
        - ``issue_count``: total number of issues detected.
        - ``healthy``: True when every provider is valid and at least one is active.
        - ``providers``: per-provider diagnostic records.
        - ``summary``: human-readable summary string.
    """
    normalized = _coerce_providers(providers)
    diagnostics = [
        _diagnose_single(entry, index)
        for index, entry in enumerate(normalized)
    ]

    active_count = sum(1 for d in diagnostics if d["activation_state"] == "active")
    inactive_count = sum(1 for d in diagnostics if d["activation_state"] == "inactive")
    configured_inactive_count = sum(
        1 for d in diagnostics if d["activation_state"] == "configured_inactive"
    )
    usable_unconfigured_count = sum(
        1 for d in diagnostics if d["activation_state"] == "usable_unconfigured"
    )
    issue_count = sum(len(d["issues"]) for d in diagnostics)
    valid_count = sum(1 for d in diagnostics if d["valid"])

    healthy = bool(diagnostics) and valid_count == len(diagnostics) and active_count >= 1

    if not diagnostics:
        summary = "No providers were provided for diagnostics."
    elif healthy:
        summary = f"All {len(diagnostics)} provider(s) are valid and at least one is active."
    else:
        summary = (
            f"{issue_count} issue(s) detected across {len(diagnostics)} provider(s); "
            f"{active_count} active, {configured_inactive_count} configured_inactive, "
            f"{usable_unconfigured_count} usable_unconfigured, {inactive_count} inactive."
        )

    return {
        "provider_count": len(diagnostics),
        "active_count": active_count,
        "inactive_count": inactive_count,
        "configured_inactive_count": configured_inactive_count,
        "usable_unconfigured_count": usable_unconfigured_count,
        "valid_count": valid_count,
        "issue_count": issue_count,
        "healthy": healthy,
        "providers": diagnostics,
        "summary": summary,
    }
