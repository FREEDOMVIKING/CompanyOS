"""Core implementation for provider activation diagnostics.

The public entry point is :func:`diagnose_provider_activation`, which accepts
provider configuration data and returns structured diagnostics describing the
activation readiness of each provider. No network access, financial actions,
or external side effects are performed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


@dataclass(frozen=True)
class ProviderActivationDiagnostics:
    """Structured result of provider activation diagnostics."""

    summary: Dict[str, Any] = field(default_factory=dict)
    providers: List[Dict[str, Any]] = field(default_factory=list)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dictionary representation."""
        return {
            "summary": dict(self.summary),
            "providers": [dict(p) for p in self.providers],
            "issues": [dict(i) for i in self.issues],
            "recommendations": list(self.recommendations),
        }


_REQUIRED_FIELDS: Tuple[str, ...] = ("provider",)


def _coerce_providers(providers: Any) -> List[Dict[str, Any]]:
    """Normalize the providers input into a list of dictionaries."""
    if providers is None:
        return []

    if isinstance(providers, Mapping):
        # A single provider mapping.
        return [_coerce_single_provider(providers)]

    if isinstance(providers, Iterable) and not isinstance(providers, (str, bytes)):
        result: List[Dict[str, Any]] = []
        for index, item in enumerate(providers):
            result.append(_coerce_single_provider(item, index=index))
        return result

    # Unsupported scalar input is treated as malformed.
    return []


def _coerce_single_provider(item: Any, index: int = 0) -> Dict[str, Any]:
    """Normalize a single provider entry, tolerating malformed input."""
    if isinstance(item, Mapping):
        return dict(item)

    return {
        "provider": f"malformed_provider_{index}",
        "_malformed": True,
        "_original_type": type(item).__name__,
    }


def _is_truthy(value: Any) -> bool:
    """Return True for explicit truthy activation signals."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "1", "on", "enabled"}
    if isinstance(value, (int, float)):
        return value != 0
    return False


def _has_credentials(provider: Mapping[str, Any]) -> bool:
    """Check whether credential-like fields are present and non-empty."""
    credential_keys = (
        "api_key",
        "apiKey",
        "token",
        "secret",
        "credentials",
        "auth_token",
    )
    for key in credential_keys:
        if key in provider:
            value = provider.get(key)
            if isinstance(value, str) and value.strip():
                return True
            if isinstance(value, Mapping) and value:
                return True
            if isinstance(value, (list, tuple)) and len(value) > 0:
                return True
            if isinstance(value, bool) and value:
                return True
    return False


def _diagnose_single(provider: Mapping[str, Any], index: int) -> Dict[str, Any]:
    """Produce diagnostics for a single provider entry."""
    name = provider.get("provider")
    if not isinstance(name, str) or not name.strip():
        name = f"unnamed_provider_{index}"

    malformed = bool(provider.get("_malformed", False))

    configured = _is_truthy(provider.get("configured", False))
    enabled = _is_truthy(provider.get("enabled", False))
    activated = _is_truthy(provider.get("activated", False))
    reachable = _is_truthy(provider.get("reachable", False))
    healthy = _is_truthy(provider.get("healthy", False))
    credentials_present = _has_credentials(provider)

    # Activation readiness: configured, credentials present, and explicitly enabled.
    activation_ready = (
        not malformed
        and configured
        and credentials_present
        and enabled
    )

    # Usable for routing: activation ready and either reachable or healthy.
    usable_for_routing = activation_ready and (reachable or healthy)

    issues: List[Dict[str, Any]] = []

    if malformed:
        issues.append({
            "provider": name,
            "code": "malformed_provider_entry",
            "severity": "high",
            "message": "Provider entry is malformed and cannot be fully evaluated.",
        })

    if not configured:
        issues.append({
            "provider": name,
            "code": "not_configured",
            "severity": "medium",
            "message": "Provider is not marked as configured.",
        })

    if not credentials_present:
        issues.append({
            "provider": name,
            "code": "missing_credentials",
            "severity": "high",
            "message": "No credential-like fields are present for this provider.",
        })

    if not enabled:
        issues.append({
            "provider": name,
            "code": "not_enabled",
            "severity": "medium",
            "message": "Provider is not explicitly enabled.",
        })

    if activation_ready and not reachable and not healthy:
        issues.append({
            "provider": name,
            "code": "activation_ready_but_unreachable",
            "severity": "low",
            "message": "Provider is activation-ready but not marked reachable or healthy.",
        })

    return {
        "provider": name,
        "index": index,
        "malformed": malformed,
        "configured": configured,
        "enabled": enabled,
        "activated": activated,
        "reachable": reachable,
        "healthy": healthy,
        "credentials_present": credentials_present,
        "activation_ready": activation_ready,
        "usable_for_routing": usable_for_routing,
        "issues": issues,
    }


def _build_recommendations(
    providers: List[Dict[str, Any]],
    issues: List[Dict[str, Any]],
) -> List[str]:
    """Derive high-level recommendations from diagnostics."""
    recommendations: List[str] = []

    if not providers:
        recommendations.append("No providers were supplied for diagnostics.")
        return recommendations

    ready_count = sum(1 for p in providers if p.get("activation_ready"))
    usable_count = sum(1 for p in providers if p.get("usable_for_routing"))

    if ready_count == 0:
        recommendations.append(
            "No providers are activation-ready; review configuration and credentials."
        )
    elif usable_count == 0:
        recommendations.append(
            "Providers are activation-ready but none are marked reachable or healthy."
        )

    if usable_count == 1:
        recommendations.append(
            "Only one provider is usable for routing; consider configuring a fallback."
        )

    high_severity = [i for i in issues if i.get("severity") == "high"]
    if high_severity:
        recommendations.append(
            f"{len(high_severity)} high-severity activation issue(s) require attention."
        )

    if not recommendations:
        recommendations.append(
            "Provider activation diagnostics look healthy; no action required."
        )

    return recommendations


def diagnose_provider_activation(
    providers: Any = None,
    *,
    include_recommendations: bool = True,
) -> ProviderActivationDiagnostics:
    """Diagnose provider activation readiness.

    Parameters
    ----------
    providers:
        Either a single provider mapping, a list of provider mappings, or
        ``None``. Malformed entries are tolerated and reported rather than
        raising.
    include_recommendations:
        When ``True`` (default), include high-level recommendations in the
        returned diagnostics.

    Returns
    -------
    ProviderActivationDiagnostics
        Structured diagnostics containing a summary, per-provider details,
        a flattened issue list, and recommendations.

    Notes
    -----
    This function performs no network access and no external actions. It
    only inspects the supplied provider metadata.
    """
    normalized = _coerce_providers(providers)

    provider_results: List[Dict[str, Any]] = []
    all_issues: List[Dict[str, Any]] = []

    for index, provider in enumerate(normalized):
        result = _diagnose_single(provider, index)
        provider_results.append(result)
        all_issues.extend(result["issues"])

    total = len(provider_results)
    ready = sum(1 for p in provider_results if p.get("activation_ready"))
    usable = sum(1 for p in provider_results if p.get("usable_for_routing"))
    malformed_count = sum(1 for p in provider_results if p.get("malformed"))

    summary: Dict[str, Any] = {
        "total_providers": total,
        "activation_ready_count": ready,
        "usable_for_routing_count": usable,
        "malformed_count": malformed_count,
        "issue_count": len(all_issues),
        "high_severity_issue_count": sum(
            1 for i in all_issues if i.get("severity") == "high"
        ),
        "healthy": total > 0 and ready == total and len(all_issues) == 0,
    }

    recommendations: List[str] = []
    if include_recommendations:
        recommendations = _build_recommendations(provider_results, all_issues)

    return ProviderActivationDiagnostics(
        summary=summary,
        providers=provider_results,
        issues=all_issues,
        recommendations=recommendations,
    )
