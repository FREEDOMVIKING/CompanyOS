"""Core implementation for provider activation diagnostics.

The public entry point is :func:`diagnose_provider_activation`, which accepts
structured provider configuration and health data and returns a structured
diagnostic report. The function is pure: it performs no I/O, no network
access, and no external actions. It safely handles empty and malformed inputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


SUPPORTED_PROVIDERS = ("openai", "local_llama")

# Issue codes that prevent a provider from being considered activated.
# Other issues (e.g. "configured_but_not_usable") are informational and do
# not by themselves block activation — they indicate a pending state.
BLOCKING_ISSUE_CODES = frozenset({
    "missing_api_key",
    "malformed_config",
    "malformed_health",
    "not_reachable",
})


def _is_dict(value: Any) -> bool:
    return isinstance(value, Mapping)


def _is_list(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes))


def _coerce_dict(value: Any) -> dict[str, Any]:
    if _is_dict(value):
        return dict(value)
    return {}


def _coerce_list(value: Any) -> list[Any]:
    if _is_list(value):
        return list(value)
    return []


def _coerce_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    return default


def _coerce_str(value: Any, default: str = "") -> str:
    if isinstance(value, str):
        return value
    return default


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _diagnose_single_provider(
    name: str,
    config: Any,
    health: Any,
) -> dict[str, Any]:
    """Build a diagnostic record for a single provider.

    ``config`` and ``health`` are expected to be mappings but any malformed
    input is tolerated and reported as an issue.
    """
    issues: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    config_malformed = False
    health_malformed = False

    if not _is_dict(config):
        config_malformed = True
        issues.append({
            "code": "malformed_config",
            "message": f"Provider '{name}' config is missing or not a mapping.",
        })
        config = {}

    if not _is_dict(health):
        health_malformed = True
        issues.append({
            "code": "malformed_health",
            "message": f"Provider '{name}' health is missing or not a mapping.",
        })
        health = {}

    configured = _coerce_bool(config.get("configured"))
    usable = _coerce_bool(health.get("usable"), configured)
    reachable = _coerce_bool(health.get("reachable"), False)
    enabled = _coerce_bool(config.get("enabled"), True)
    api_key_present = _coerce_bool(config.get("api_key_present"), False)
    base_url = _coerce_str(config.get("base_url"), "")
    health_status = _coerce_str(health.get("status"), "")
    last_error = _coerce_str(health.get("last_error"), "")
    timeout_seconds = _coerce_int(config.get("timeout_seconds"), 0)

    if not enabled:
        warnings.append({
            "code": "provider_disabled",
            "message": f"Provider '{name}' is disabled in configuration.",
        })

    # Only flag missing API key when the provider is actually configured —
    # an unconfigured provider is simply "not_configured", not blocked.
    if name == "openai" and configured and not api_key_present:
        issues.append({
            "code": "missing_api_key",
            "message": "OpenAI provider is configured without an API key.",
        })

    if not base_url and name == "local_llama":
        warnings.append({
            "code": "missing_base_url",
            "message": "Local LLaMA provider has no base_url configured.",
        })

    if configured and not usable:
        issues.append({
            "code": "configured_but_not_usable",
            "message": f"Provider '{name}' is configured but not reported usable.",
        })

    if usable and not reachable and name == "local_llama":
        issues.append({
            "code": "not_reachable",
            "message": f"Provider '{name}' is usable but not reachable.",
        })

    if last_error:
        warnings.append({
            "code": "recent_error",
            "message": f"Provider '{name}' reported a recent error: {last_error}",
        })

    if timeout_seconds <= 0:
        warnings.append({
            "code": "invalid_timeout",
            "message": f"Provider '{name}' has no positive timeout configured.",
        })

    has_blocking = any(
        issue["code"] in BLOCKING_ISSUE_CODES for issue in issues
    )

    # State precedence:
    #   1. disabled — explicitly turned off
    #   2. activation_blocked — blocking issues (including malformed input)
    #   3. not_configured — no blocking issues and not configured
    #   4. activated — usable with no blocking issues
    #   5. pending_activation — configured/enabled but not yet usable
    if not enabled:
        activation_state = "disabled"
    elif has_blocking:
        activation_state = "activation_blocked"
    elif not configured:
        activation_state = "not_configured"
    elif usable:
        activation_state = "activated"
    else:
        # Configured and enabled with no blocking issues, but not yet usable.
        activation_state = "pending_activation"

    return {
        "provider": name,
        "activation_state": activation_state,
        "configured": configured,
        "enabled": enabled,
        "usable": usable,
        "reachable": reachable,
        "api_key_present": api_key_present,
        "base_url": base_url,
        "health_status": health_status,
        "last_error": last_error,
        "timeout_seconds": timeout_seconds,
        "issues": issues,
        "warnings": warnings,
    }


def _derive_summary(providers: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(providers)
    activated = sum(1 for p in providers if p["activation_state"] == "activated")
    blocked = sum(1 for p in providers if p["activation_state"] == "activation_blocked")
    pending = sum(1 for p in providers if p["activation_state"] == "pending_activation")
    disabled = sum(1 for p in providers if p["activation_state"] == "disabled")
    not_configured = sum(
        1 for p in providers if p["activation_state"] == "not_configured"
    )

    issue_count = sum(len(p["issues"]) for p in providers)
    warning_count = sum(len(p["warnings"]) for p in providers)

    primary = next(
        (p for p in providers if p["provider"] == "openai"),
        None,
    )
    fallback = next(
        (p for p in providers if p["provider"] == "local_llama"),
        None,
    )

    primary_ready = bool(primary and primary["activation_state"] == "activated")
    fallback_ready = bool(fallback and fallback["activation_state"] == "activated")

    if primary_ready:
        routing_recommendation = "primary_available"
    elif fallback_ready:
        routing_recommendation = "fallback_only"
    elif primary and primary["activation_state"] == "pending_activation":
        routing_recommendation = "awaiting_primary_activation"
    else:
        routing_recommendation = "no_active_provider"

    overall_state: str
    if primary_ready or fallback_ready:
        overall_state = "operational"
    elif blocked > 0:
        overall_state = "degraded"
    elif pending > 0:
        overall_state = "pending"
    else:
        overall_state = "inactive"

    return {
        "overall_state": overall_state,
        "routing_recommendation": routing_recommendation,
        "primary_ready": primary_ready,
        "fallback_ready": fallback_ready,
        "provider_count": total,
        "activated_count": activated,
        "blocked_count": blocked,
        "pending_count": pending,
        "disabled_count": disabled,
        "not_configured_count": not_configured,
        "issue_count": issue_count,
        "warning_count": warning_count,
    }


@dataclass(frozen=True)
class ActivationDiagnosticsResult:
    """Structured result returned by :func:`diagnose_provider_activation`."""

    success: bool
    status: str
    summary: dict[str, Any] = field(default_factory=dict)
    providers: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "status": self.status,
            "summary": self.summary,
            "providers": self.providers,
            "recommendations": self.recommendations,
            "errors": self.errors,
        }


def _build_recommendations(
    providers: list[dict[str, Any]],
    summary: dict[str, Any],
) -> list[str]:
    recs: list[str] = []

    if summary["routing_recommendation"] == "no_active_provider":
        recs.append(
            "No provider is currently activated. Configure at least one "
            "provider before routing internal work."
        )

    if summary["routing_recommendation"] == "fallback_only":
        recs.append(
            "Primary provider is not activated. Investigate OpenAI activation "
            "while relying on the local fallback."
        )

    if summary["routing_recommendation"] == "awaiting_primary_activation":
        recs.append(
            "Primary provider activation is pending. Resolve outstanding "
            "issues to restore primary routing."
        )

    for provider in providers:
        for issue in provider["issues"]:
            recs.append(
                f"[{provider['provider']}] {issue['code']}: {issue['message']}"
            )

    if not recs:
        recs.append("Provider activation diagnostics completed with no actions required.")

    return recs


def diagnose_provider_activation(
    provider_config: Any = None,
    provider_health: Any = None,
    *,
    providers: Any = None,
) -> ActivationDiagnosticsResult:
    """Diagnose provider activation state from configuration and health data.

    Parameters
    ----------
    provider_config:
        Mapping of provider name to configuration dict. Expected keys per
        provider include ``configured``, ``enabled``, ``api_key_present``,
        ``base_url``, and ``timeout_seconds``. Malformed or missing values
        are tolerated.
    provider_health:
        Mapping of provider name to health dict. Expected keys per provider
        include ``usable``, ``reachable``, ``status``, and ``last_error``.
        Malformed or missing values are tolerated.
    providers:
        Optional explicit list of provider names to diagnose. When omitted,
        the union of keys from ``provider_config`` and ``provider_health`` is
        used, falling back to the supported providers.

    Returns
    -------
    ActivationDiagnosticsResult
        Structured diagnostic result with summary, per-provider details,
        recommendations, and errors. The function never raises on malformed
        input; instead it records diagnostic issues.

    Notes
    -----
    This function performs no network access, no financial actions, and no
    external actions. It is safe to call in any internal CompanyOS context.
    """
    errors: list[str] = []

    config_map = _coerce_dict(provider_config)
    health_map = _coerce_dict(provider_health)

    if not _is_dict(provider_config) and provider_config is not None:
        errors.append("provider_config was not a mapping; treated as empty.")

    if not _is_dict(provider_health) and provider_health is not None:
        errors.append("provider_health was not a mapping; treated as empty.")

    if providers is not None:
        provider_names = [str(p) for p in _coerce_list(providers)]
    else:
        names = set(config_map.keys()) | set(health_map.keys())
        provider_names = sorted(names) if names else list(SUPPORTED_PROVIDERS)

    if not provider_names:
        errors.append("No providers supplied for diagnostics.")

    provider_records: list[dict[str, Any]] = []
    for name in provider_names:
        provider_records.append(
            _diagnose_single_provider(
                name=name,
                config=config_map.get(name, {}),
                health=health_map.get(name, {}),
            )
        )

    summary = _derive_summary(provider_records)
    recommendations = _build_recommendations(provider_records, summary)

    success = (
        summary["issue_count"] == 0
        and summary["activated_count"] > 0
        and bool(provider_records)
    )
    status = "provider_activation_diagnostics_complete"

    return ActivationDiagnosticsResult(
        success=success,
        status=status,
        summary=summary,
        providers=provider_records,
        recommendations=recommendations,
        errors=errors,
    )
