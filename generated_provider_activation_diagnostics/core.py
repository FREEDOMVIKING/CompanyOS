"""Core implementation for provider_activation_diagnostics."""

from __future__ import annotations

from typing import Any

__all__ = ["diagnose_provider_activation"]


_KNOWN_PROVIDERS = {"openai", "local_llama", "anthropic", "azure_openai"}

_VALID_ACTIVATION_STATES = {
    "inactive",
    "configured",
    "activating",
    "active",
    "degraded",
    "failed",
    "unknown",
}


def _is_dict(value: Any) -> bool:
    return isinstance(value, dict)


def _coerce_provider_entry(provider_name: Any, entry: Any) -> dict[str, Any] | None:
    """Normalize a single provider entry into a diagnostic record.

    Returns None when the entry is too malformed to evaluate.
    """
    if not isinstance(provider_name, str) or not provider_name.strip():
        return None

    name = provider_name.strip()

    if entry is None:
        entry = {}

    if not _is_dict(entry):
        return {
            "provider": name,
            "known": name in _KNOWN_PROVIDERS,
            "activation_state": "unknown",
            "configured": False,
            "usable": False,
            "issues": [
                {
                    "code": "malformed_entry",
                    "severity": "high",
                    "message": "Provider entry is not a dict; cannot evaluate activation.",
                }
            ],
            "recommendations": [
                "Provide provider configuration as a dict with activation_state and configured fields."
            ],
        }

    activation_state = entry.get("activation_state", "unknown")
    if not isinstance(activation_state, str):
        activation_state = "unknown"
    activation_state = activation_state.strip().lower()
    if activation_state not in _VALID_ACTIVATION_STATES:
        activation_state = "unknown"

    configured = entry.get("configured")
    configured = configured is True

    reachable = entry.get("reachable")
    reachable = reachable is True

    credentials_present = entry.get("credentials_present")
    credentials_present = credentials_present is True

    last_error = entry.get("last_error")
    if last_error is not None and not isinstance(last_error, str):
        last_error = str(last_error)

    issues: list[dict[str, Any]] = []
    recommendations: list[str] = []

    if name not in _KNOWN_PROVIDERS:
        issues.append(
            {
                "code": "unknown_provider",
                "severity": "medium",
                "message": f"Provider '{name}' is not in the known provider set.",
            }
        )
        recommendations.append(
            f"Confirm whether '{name}' is an intended provider before activation."
        )

    if not configured:
        issues.append(
            {
                "code": "not_configured",
                "severity": "high",
                "message": "Provider is not configured.",
            }
        )
        recommendations.append("Complete provider configuration before activation.")

    if configured and not credentials_present:
        issues.append(
            {
                "code": "missing_credentials",
                "severity": "high",
                "message": "Provider is configured but credentials are missing.",
            }
        )
        recommendations.append("Supply valid credentials for the provider.")

    if activation_state == "failed":
        issues.append(
            {
                "code": "activation_failed",
                "severity": "high",
                "message": "Provider activation reported a failure.",
            }
        )
        if last_error:
            recommendations.append(f"Investigate last error: {last_error}")
        else:
            recommendations.append("Review provider logs for activation failure details.")

    if activation_state == "degraded":
        issues.append(
            {
                "code": "activation_degraded",
                "severity": "medium",
                "message": "Provider activation is degraded.",
            }
        )
        recommendations.append("Monitor provider health and consider fallback routing.")

    if activation_state == "activating":
        issues.append(
            {
                "code": "activation_in_progress",
                "severity": "low",
                "message": "Provider activation is still in progress.",
            }
        )
        recommendations.append("Wait for activation to complete before routing work.")

    if activation_state == "active" and not reachable:
        issues.append(
            {
                "code": "active_but_unreachable",
                "severity": "high",
                "message": "Provider is marked active but reported unreachable.",
            }
        )
        recommendations.append("Verify connectivity before relying on this provider.")

    if activation_state == "inactive" and configured and credentials_present:
        issues.append(
            {
                "code": "inactive_but_ready",
                "severity": "low",
                "message": "Provider is configured with credentials but remains inactive.",
            }
        )
        recommendations.append("Trigger activation if this provider is intended for use.")

    usable = (
        configured
        and credentials_present
        and activation_state in {"active", "degraded"}
        and reachable
    )

    return {
        "provider": name,
        "known": name in _KNOWN_PROVIDERS,
        "activation_state": activation_state,
        "configured": configured,
        "credentials_present": credentials_present,
        "reachable": reachable,
        "usable": usable,
        "last_error": last_error,
        "issues": issues,
        "recommendations": recommendations,
    }


def diagnose_provider_activation(providers: Any | None = None) -> dict[str, Any]:
    """Diagnose provider activation state from supplied provider data.

    This function performs no network or external actions. It evaluates the
    provider configuration and activation signals provided by the caller and
    returns structured diagnostic data.

    Args:
        providers: Either a dict mapping provider names to provider entry dicts,
            or a list of provider entry dicts each containing a "provider" or
            "name" field. ``None`` or empty input is handled safely.

    Returns:
        A structured dict with the following shape::

            {
                "success": bool,
                "status": str,
                "provider_count": int,
                "usable_count": int,
                "issue_count": int,
                "providers": [ ... per-provider diagnostics ... ],
                "summary": { ... },
                "recommendations": [ ... global recommendations ... ],
            }
    """
    if providers is None:
        providers = {}

    # Safe handling of malformed string input.
    if isinstance(providers, str):
        return {
            "success": True,
            "status": "provider_activation_diagnostics_empty",
            "provider_count": 0,
            "usable_count": 0,
            "issue_count": 0,
            "providers": [],
            "summary": {
                "healthy": True,
                "note": "No providers supplied; nothing to diagnose.",
            },
            "recommendations": [
                "Provide a dict or list of provider configurations to diagnose."
            ],
            "malformed_input": True,
        }

    entries: list[tuple[str, Any]] = []

    if _is_dict(providers):
        for key, value in providers.items():
            entries.append((key, value))
    elif isinstance(providers, list):
        for item in providers:
            if not _is_dict(item):
                # Skip malformed list entries but continue processing others.
                continue
            name = item.get("provider") or item.get("name")
            if not isinstance(name, str) or not name.strip():
                continue
            # Build a copy without the name fields to avoid duplication.
            entry = {
                k: v
                for k, v in item.items()
                if k not in {"provider", "name"}
            }
            entries.append((name, entry))
    else:
        # Unknown container type; handle safely as empty.
        return {
            "success": True,
            "status": "provider_activation_diagnostics_empty",
            "provider_count": 0,
            "usable_count": 0,
            "issue_count": 0,
            "providers": [],
            "summary": {
                "healthy": True,
                "note": "Unsupported providers input type; nothing to diagnose.",
            },
            "recommendations": [
                "Provide providers as a dict or a list of dicts."
            ],
            "malformed_input": True,
        }

    diagnostics: list[dict[str, Any]] = []
    seen: set[str] = set()

    for name, entry in entries:
        record = _coerce_provider_entry(name, entry)
        if record is None:
            continue
        if record["provider"] in seen:
            continue
        seen.add(record["provider"])
        diagnostics.append(record)

    # Stable ordering by provider name for deterministic output.
    diagnostics.sort(key=lambda r: r["provider"])

    total_issues = sum(len(r["issues"]) for r in diagnostics)
    usable_count = sum(1 for r in diagnostics if r["usable"])
    high_severity = [
        {"provider": r["provider"], "issues": r["issues"]}
        for r in diagnostics
        if any(i.get("severity") == "high" for i in r["issues"])
    ]

    global_recommendations: list[str] = []
    if not diagnostics:
        global_recommendations.append(
            "No providers were supplied or all entries were malformed."
        )
    if usable_count == 0 and diagnostics:
        global_recommendations.append(
            "No providers are currently usable; ensure at least one provider is configured and active."
        )
    if high_severity:
        global_recommendations.append(
            "Resolve high-severity activation issues before routing work to affected providers."
        )

    healthy = (total_issues == 0 and usable_count > 0) if diagnostics else True

    summary = {
        "healthy": healthy,
        "provider_count": len(diagnostics),
        "usable_count": usable_count,
        "issue_count": total_issues,
        "high_severity_providers": [r["provider"] for r in high_severity],
    }

    return {
        "success": True,
        "status": "provider_activation_diagnostics_complete",
        "provider_count": len(diagnostics),
        "usable_count": usable_count,
        "issue_count": total_issues,
        "providers": diagnostics,
        "summary": summary,
        "recommendations": global_recommendations,
    }
