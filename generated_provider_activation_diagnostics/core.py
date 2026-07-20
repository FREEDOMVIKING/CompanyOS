"""Core implementation for provider activation diagnostics.

This module provides a single public function, ``diagnose_provider_activation``,
that inspects provider activation data and returns structured diagnostic
information. It performs no network access, no financial actions, and no
external actions of any kind.
"""

from __future__ import annotations

from typing import Any


VALID_PROVIDERS = {"openai", "local_llama", "anthropic", "azure_openai"}

VALID_STATUSES = {"active", "inactive", "degraded", "unconfigured", "unknown"}


def _coerce_dict(value: Any) -> dict[str, Any]:
    """Return *value* as a dict, or an empty dict when malformed."""
    if isinstance(value, dict):
        return value
    return {}


def _coerce_list(value: Any) -> list[Any]:
    """Return *value* as a list, or an empty list when malformed."""
    if isinstance(value, list):
        return value
    return []


def _coerce_str(value: Any) -> str:
    """Return *value* as a stripped string, or empty string when not a string."""
    if isinstance(value, str):
        return value.strip()
    return ""


def _coerce_bool(value: Any) -> bool:
    """Return *value* as a bool, defaulting to False for non-bool values."""
    return bool(value) if isinstance(value, bool) else False


def _diagnose_single_provider(provider_entry: Any) -> dict[str, Any]:
    """Diagnose a single provider entry.

    Parameters
    ----------
    provider_entry
        A dict-like object describing a single provider. Expected keys:
        ``provider``, ``status``, ``configured``, ``usable``, ``reachable``.

    Returns
    -------
    dict
        Structured diagnostic for the provider.
    """
    entry = _coerce_dict(provider_entry)

    provider_name = _coerce_str(entry.get("provider")) or "unknown"
    status = _coerce_str(entry.get("status")) or "unknown"
    configured = _coerce_bool(entry.get("configured"))
    usable = _coerce_bool(entry.get("usable"))
    reachable = _coerce_bool(entry.get("reachable"))

    issues: list[str] = []
    recommendations: list[str] = []

    if provider_name not in VALID_PROVIDERS:
        issues.append("unknown_provider_name")
        recommendations.append(
            f"Provider '{provider_name}' is not in the known provider set."
        )

    if status not in VALID_STATUSES:
        issues.append("invalid_status")
        recommendations.append(
            f"Status '{status}' is not recognized; expected one of {sorted(VALID_STATUSES)}."
        )

    if not configured:
        issues.append("provider_not_configured")
        recommendations.append(
            f"Provider '{provider_name}' is not configured."
        )

    if configured and not usable:
        issues.append("configured_but_not_usable")
        recommendations.append(
            f"Provider '{provider_name}' is configured but not usable."
        )

    if not reachable:
        issues.append("provider_not_reachable")
        recommendations.append(
            f"Provider '{provider_name}' is not reachable."
        )

    if status == "degraded":
        issues.append("provider_degraded")
        recommendations.append(
            f"Provider '{provider_name}' is degraded; consider fallback."
        )

    if status == "inactive" and configured:
        issues.append("configured_but_inactive")
        recommendations.append(
            f"Provider '{provider_name}' is configured but inactive."
        )

    healthy = len(issues) == 0

    return {
        "provider": provider_name,
        "status": status,
        "configured": configured,
        "usable": usable,
        "reachable": reachable,
        "healthy": healthy,
        "issues": issues,
        "recommendations": recommendations,
    }


def diagnose_provider_activation(
    provider_data: Any,
    *,
    fallback_provider: str | None = None,
) -> dict[str, Any]:
    """Diagnose provider activation state from structured input.

    This function inspects provider activation/health data and returns a
    structured diagnostic report. It does **not** perform any network,
    financial, or external actions.

    Parameters
    ----------
    provider_data
        Structured data describing providers. Accepts either:

        * A dict with a ``providers`` key containing a list of provider
          entries, e.g.::

              {
                  "providers": [
                      {"provider": "openai", "status": "active",
                       "configured": True, "usable": True,
                       "reachable": True}
                  ]
              }

        * A dict with ``primary`` and/or ``fallback`` sub-dicts, e.g.::

              {
                  "primary": {"provider": "openai", ...},
                  "fallback": {"provider": "local_llama", ...}
              }

        * A list of provider entry dicts.

    fallback_provider
        Optional name of a fallback provider to flag in the report.

    Returns
    -------
    dict
        A structured diagnostic report with keys:
        ``success``, ``provider_count``, ``healthy_count``, ``unhealthy_count``,
        ``providers``, ``fallback_provider``, ``overall_healthy``, and
        ``recommendations``.
    """
    # Normalize input into a list of provider entries.
    entries: list[Any] = []

    if isinstance(provider_data, list):
        entries = provider_data
    elif isinstance(provider_data, dict):
        if "providers" in provider_data and isinstance(
            provider_data["providers"], list
        ):
            entries = provider_data["providers"]
        else:
            # Look for primary/fallback style.
            for key in ("primary", "fallback"):
                sub = provider_data.get(key)
                if isinstance(sub, dict):
                    entries.append(sub)
                elif sub is not None:
                    # Malformed sub-entry; still try to coerce.
                    entries.append(sub)
    else:
        # Empty or malformed top-level input.
        entries = []

    diagnostics = [_diagnose_single_provider(entry) for entry in entries]

    healthy_count = sum(1 for d in diagnostics if d["healthy"])
    unhealthy_count = len(diagnostics) - healthy_count

    all_recommendations: list[str] = []
    for d in diagnostics:
        all_recommendations.extend(d["recommendations"])

    overall_healthy = len(diagnostics) > 0 and unhealthy_count == 0

    # If no providers at all, add a recommendation.
    if len(diagnostics) == 0:
        all_recommendations.append(
            "No provider data was supplied; cannot determine activation state."
        )

    # If a fallback provider is specified, verify it appears.
    if fallback_provider is not None:
        fallback_names = {d["provider"] for d in diagnostics}
        if fallback_provider not in fallback_names:
            all_recommendations.append(
                f"Fallback provider '{fallback_provider}' is not present in the provider data."
            )

    return {
        "success": True,
        "status": "provider_activation_diagnostics_complete",
        "provider_count": len(diagnostics),
        "healthy_count": healthy_count,
        "unhealthy_count": unhealthy_count,
        "overall_healthy": overall_healthy,
        "fallback_provider": fallback_provider,
        "providers": diagnostics,
        "recommendations": all_recommendations,
        "external_actions_performed": False,
        "network_access_performed": False,
        "financial_actions_performed": False,
    }
