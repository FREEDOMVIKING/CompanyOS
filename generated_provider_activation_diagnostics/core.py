"""Core implementation for provider activation diagnostics.

The public entry point is :func:`diagnose_provider_activation`, which
inspects provider configuration data and returns a structured diagnostic
report.  No network access, financial actions, or external side effects
are performed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Sequence


_REQUIRED_PROVIDER_FIELDS = ("provider",)
_OPTIONAL_PROVIDER_FIELDS = (
    "configured",
    "usable",
    "reachable",
    "enabled",
    "healthy",
    "status",
    "base_url",
    "note",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _coerce_providers(
    providers: Any,
) -> List[Dict[str, Any]]:
    """Normalize the *providers* argument into a list of dicts.

    Accepts ``None``, a single mapping, or a sequence of mappings.
    Malformed entries are replaced with safe placeholder dicts so that
    callers always receive a structured response.
    """
    if providers is None:
        return []

    if isinstance(providers, Mapping):
        # A single provider mapping.
        return [_coerce_single_provider(providers)]

    if isinstance(providers, Sequence) and not isinstance(providers, (str, bytes)):
        result: List[Dict[str, Any]] = []
        for index, item in enumerate(providers):
            if isinstance(item, Mapping):
                result.append(_coerce_single_provider(item))
            else:
                result.append(
                    {
                        "provider": f"malformed_{index}",
                        "malformed": True,
                        "error": "provider entry is not a mapping",
                        "raw_type": type(item).__name__,
                    }
                )
        return result

    # Completely unexpected input type.
    return [
        {
            "provider": "malformed_input",
            "malformed": True,
            "error": "providers argument must be a mapping or sequence of mappings",
            "raw_type": type(providers).__name__,
        }
    ]


def _coerce_single_provider(item: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate and normalize a single provider mapping."""
    if not isinstance(item, Mapping):
        return {
            "provider": "malformed",
            "malformed": True,
            "error": "provider entry is not a mapping",
            "raw_type": type(item).__name__,
        }

    provider_name = item.get("provider")
    if not isinstance(provider_name, str) or not provider_name.strip():
        return {
            "provider": "unknown",
            "malformed": True,
            "error": "missing or invalid 'provider' field",
            "raw": dict(item) if isinstance(item, Mapping) else None,
        }

    normalized: Dict[str, Any] = {"provider": provider_name}

    for field in _OPTIONAL_PROVIDER_FIELDS:
        if field in item:
            normalized[field] = item[field]

    normalized["malformed"] = False
    return normalized


def _evaluate_activation(provider: Dict[str, Any]) -> Dict[str, Any]:
    """Determine activation state for a single normalized provider."""
    if provider.get("malformed"):
        return {
            "activated": False,
            "activation_state": "invalid",
            "issues": [provider.get("error", "malformed provider entry")],
        }

    issues: List[str] = []

    configured = bool(provider.get("configured", False))
    enabled = bool(provider.get("enabled", True))
    usable = bool(provider.get("usable", False))
    reachable = bool(provider.get("reachable", False))
    healthy = bool(provider.get("healthy", True))

    if not configured:
        issues.append("provider_not_configured")
    if not enabled:
        issues.append("provider_disabled")
    if not usable:
        issues.append("provider_not_usable")
    if not reachable:
        issues.append("provider_not_reachable")
    if not healthy:
        issues.append("provider_unhealthy")

    if not issues:
        state = "activated"
        activated = True
    elif configured and enabled and usable and healthy and not reachable:
        state = "degraded"
        activated = True
    elif configured and not enabled:
        state = "standby"
        activated = False
    elif configured and enabled and usable:
        state = "partial"
        activated = True
    elif configured and enabled:
        state = "standby"
        activated = False
    elif configured:
        state = "inactive"
        activated = False
    else:
        state = "unconfigured"
        activated = False

    return {
        "activated": activated,
        "activation_state": state,
        "issues": issues,
    }


def diagnose_provider_activation(
    providers: Any = None,
    *,
    routing_policy: Any = None,
) -> Dict[str, Any]:
    """Diagnose provider activation state from configuration data.

    Parameters
    ----------
    providers:
        Either ``None``, a single provider mapping, or a sequence of
        provider mappings.  Each mapping should contain at least a
        ``"provider"`` string field.  Optional fields include
        ``configured``, ``usable``, ``reachable``, ``enabled``,
        ``healthy``, ``status``, ``base_url``, and ``note``.

    routing_policy:
        Optional routing policy descriptor (mapping or string).  It is
        included verbatim in the report when provided.

    Returns
    -------
    dict
        A structured diagnostic report with the following keys:

        - ``generated_at``: ISO timestamp.
        - ``provider_count``: number of providers evaluated.
        - ``activated_count``: number of activated providers.
        - ``healthy``: ``True`` when all providers are activated.
        - ``providers``: per-provider diagnostic details.
        - ``routing_policy``: normalized routing policy if provided.
        - ``issues``: aggregate list of all issues found.
    """
    normalized_providers = _coerce_providers(providers)

    diagnostics: List[Dict[str, Any]] = []
    all_issues: List[str] = []
    activated_count = 0

    for provider in normalized_providers:
        activation = _evaluate_activation(provider)
        if activation["activated"]:
            activated_count += 1
        all_issues.extend(
            f"{provider.get('provider', 'unknown')}:{issue}"
            for issue in activation.get("issues", [])
        )
        diagnostics.append({**provider, **activation})

    normalized_policy: Optional[Dict[str, Any]] = None
    if routing_policy is not None:
        if isinstance(routing_policy, Mapping):
            normalized_policy = dict(routing_policy)
        elif isinstance(routing_policy, str):
            normalized_policy = {"policy": routing_policy}
        else:
            normalized_policy = {
                "malformed": True,
                "raw_type": type(routing_policy).__name__,
                "error": "routing_policy must be a mapping or string",
            }

    report: Dict[str, Any] = {
        "generated_at": _now(),
        "provider_count": len(normalized_providers),
        "activated_count": activated_count,
        "healthy": len(normalized_providers) > 0 and activated_count == len(normalized_providers),
        "providers": diagnostics,
        "routing_policy": normalized_policy,
        "issues": all_issues,
        "external_actions_performed": False,
        "network_access_performed": False,
    }

    return report
