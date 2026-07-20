"""Core implementation for provider_activation_diagnostics.

This module inspects provider activation records and produces structured
diagnostics. It performs no network access, no financial actions, and no
external actions of any kind.
"""
from __future__ import annotations

from typing import Any

REQUIRED_FIELDS = ("provider", "status")
VALID_STATUSES = ("active", "inactive", "error", "pending", "unknown")


def _is_dict(value: Any) -> bool:
    return isinstance(value, dict)


def _coerce_providers(providers: Any) -> list[dict[str, Any]]:
    """Normalize the providers input into a list of dicts.

    Accepts None, non-list values, lists of dicts, and dicts keyed by provider
    name. Malformed entries are replaced with sentinel dicts so diagnostics can
    report them rather than crash.
    """
    if providers is None:
        return []

    if _is_dict(providers):
        result: list[dict[str, Any]] = []
        for key, value in providers.items():
            if _is_dict(value):
                merged = dict(value)
                merged.setdefault("provider", str(key))
                result.append(merged)
            else:
                result.append({"provider": str(key), "status": "unknown", "malformed": True})
        return result

    if isinstance(providers, list):
        normalized: list[dict[str, Any]] = []
        for item in providers:
            if _is_dict(item):
                normalized.append(dict(item))
            else:
                normalized.append({"provider": str(item), "status": "unknown", "malformed": True})
        return normalized

    # Unknown top-level type: treat as a single malformed entry.
    return [{"provider": "unknown", "status": "unknown", "malformed": True}]


def _diagnose_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Produce a diagnostic record for a single provider entry."""
    issues: list[str] = []
    warnings: list[str] = []

    provider_name = entry.get("provider")
    if not provider_name or not isinstance(provider_name, str):
        issues.append("missing_or_non_string_provider")
        provider_name = "unknown"

    status = entry.get("status", "unknown")
    if not isinstance(status, str):
        issues.append("non_string_status")
        status = "unknown"

    if status not in VALID_STATUSES:
        issues.append(f"invalid_status:{status}")
        status = "unknown"

    for field in REQUIRED_FIELDS:
        if field not in entry:
            issues.append(f"missing_field:{field}")

    if entry.get("malformed") is True:
        issues.append("malformed_entry")

    config = entry.get("config")
    if config is not None and not _is_dict(config):
        issues.append("non_dict_config")

    credentials = entry.get("credentials")
    if credentials is not None and not _is_dict(credentials):
        warnings.append("non_dict_credentials")

    enabled = entry.get("enabled")
    if enabled is not None and not isinstance(enabled, bool):
        warnings.append("non_bool_enabled")

    activated = status == "active"
    if activated and enabled is False:
        warnings.append("active_but_disabled")

    if status == "error" and not entry.get("error_detail"):
        warnings.append("error_status_without_detail")

    healthy = len(issues) == 0 and status in ("active", "inactive", "pending")

    return {
        "provider": provider_name,
        "status": status,
        "activated": activated,
        "healthy": healthy,
        "issues": issues,
        "warnings": warnings,
        "raw": entry,
    }


def diagnose_provider_activation(providers: Any = None) -> dict[str, Any]:
    """Diagnose provider activation records.

    Args:
        providers: Optional collection of provider activation records. May be a
            list of dicts, a dict keyed by provider name, None, or any other
            value (handled safely as malformed input).

    Returns:
        A structured dict containing:
          - success: always True (diagnostics ran successfully)
          - summary: aggregate counts
          - providers: per-provider diagnostic records
          - issues: flat list of all issues found
          - recommendations: suggested next internal steps
    """
    entries = _coerce_providers(providers)
    diagnostics = [_diagnose_entry(e) for e in entries]

    total = len(diagnostics)
    active = sum(1 for d in diagnostics if d["activated"])
    healthy = sum(1 for d in diagnostics if d["healthy"])
    with_issues = sum(1 for d in diagnostics if d["issues"])
    with_warnings = sum(1 for d in diagnostics if d["warnings"])

    all_issues: list[dict[str, str]] = []
    for d in diagnostics:
        for issue in d["issues"]:
            all_issues.append({"provider": d["provider"], "issue": issue})

    recommendations: list[str] = []
    if total == 0:
        recommendations.append("No provider records supplied; nothing to diagnose.")
    if with_issues:
        recommendations.append("Resolve malformed or invalid provider entries before activation.")
    if active == 0 and total > 0:
        recommendations.append("No providers are currently active.")
    if any(d["status"] == "error" for d in diagnostics):
        recommendations.append("Review providers in error state and attach error_detail.")
    if any("active_but_disabled" in d["warnings"] for d in diagnostics):
        recommendations.append("Reconcile providers marked active but disabled.")
    if not recommendations:
        recommendations.append("All provider activation records are well-formed.")

    return {
        "success": True,
        "status": "provider_activation_diagnostics_complete",
        "summary": {
            "total": total,
            "active": active,
            "inactive_or_other": total - active,
            "healthy": healthy,
            "with_issues": with_issues,
            "with_warnings": with_warnings,
        },
        "providers": diagnostics,
        "issues": all_issues,
        "recommendations": recommendations,
        "external_actions_performed": False,
    }
