"""Core implementation for provider_activation_diagnostics.

The public entry point is :func:`diagnose_provider_activation`, which accepts a
provider configuration mapping and returns a structured diagnostic report.
"""

from __future__ import annotations

from typing import Any


def _safe_bool(value: Any) -> bool:
    """Coerce a value to bool, treating common falsy strings as False."""
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "on", "enabled"}
    return bool(value)


def _safe_int(value: Any, default: int = 0) -> int:
    """Coerce a value to int, returning *default* on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _is_dict(value: Any) -> bool:
    return isinstance(value, dict)


def _diagnose_single_provider(
    provider_id: str,
    provider_cfg: Any,
) -> dict[str, Any]:
    """Diagnose a single provider entry.

    Parameters
    ----------
    provider_id:
        Identifier for the provider (key from the config mapping).
    provider_cfg:
        The provider configuration value.  Expected to be a dict but malformed
        inputs are handled gracefully.
    """
    diagnosis: dict[str, Any] = {
        "provider_id": provider_id,
        "valid": False,
        "activated": False,
        "issues": [],
        "recommendations": [],
    }

    if not _is_dict(provider_cfg):
        diagnosis["issues"].append("provider_config_not_dict")
        diagnosis["recommendations"].append(
            "Provide provider configuration as a dictionary."
        )
        return diagnosis

    diagnosis["valid"] = True

    # --- Activation flag -------------------------------------------------
    activated = _safe_bool(provider_cfg.get("activated"))
    diagnosis["activated"] = activated

    if not activated:
        diagnosis["issues"].append("not_activated")
        diagnosis["recommendations"].append(
            "Set 'activated' to true once the provider is ready for use."
        )

    # --- Local provider flag --------------------------------------------
    is_local = _safe_bool(provider_cfg.get("local"))

    # --- API key / credentials -------------------------------------------
    api_key = provider_cfg.get("api_key")
    has_api_key = bool(api_key) and str(api_key).strip() != ""
    if not has_api_key and not is_local:
        diagnosis["issues"].append("missing_api_key")
        diagnosis["recommendations"].append(
            "Configure a non-empty 'api_key' for this provider."
        )

    # --- Priority --------------------------------------------------------
    priority = _safe_int(provider_cfg.get("priority"), default=-1)
    if priority < 0:
        diagnosis["issues"].append("invalid_priority")
        diagnosis["recommendations"].append(
            "Set a non-negative integer 'priority' for routing decisions."
        )

    # --- Fallback configuration ------------------------------------------
    is_fallback = _safe_bool(provider_cfg.get("fallback"))
    if is_fallback and not has_api_key and not is_local:
        diagnosis["issues"].append("fallback_without_credentials")
        diagnosis["recommendations"].append(
            "Fallback providers should either have credentials or be marked 'local'."
        )

    # --- Usability summary -----------------------------------------------
    usable = activated and (has_api_key or is_local)
    diagnosis["usable"] = usable

    return diagnosis


def diagnose_provider_activation(
    providers: Any | None = None,
    *,
    routing_policy: Any | None = None,
) -> dict[str, Any]:
    """Diagnose provider activation state from configuration data.

    This function is purely diagnostic.  It does **not** make network requests,
    perform financial actions, or modify any external state.

    Parameters
    ----------
    providers:
        A mapping of provider identifiers to provider configuration dicts.
        Example::

            {
                "openai": {
                    "activated": True,
                    "api_key": "sk-...",
                    "priority": 1,
                },
                "local_llama": {
                    "activated": True,
                    "local": True,
                    "fallback": True,
                    "priority": 2,
                },
            }

    routing_policy:
        Optional routing policy descriptor (dict).  When provided, the
        diagnostic report will include a policy compatibility check.

    Returns
    -------
    dict
        A structured diagnostic report with the following top-level keys:

        - ``success`` (bool) – always ``True``; the function never raises.
        - ``status`` (str) – ``"provider_activation_diagnostics_complete"``.
        - ``provider_count`` (int) – number of provider entries evaluated.
        - ``activated_count`` (int) – number of providers marked activated.
        - ``usable_count`` (int) – number of providers deemed usable.
        - ``providers`` (list[dict]) – per-provider diagnostic details.
        - ``issues`` (list[str]) – aggregate issue identifiers.
        - ``recommendations`` (list[str]) – aggregate recommendations.
        - ``routing_policy_compatible`` (bool | None) – ``None`` when no
          routing policy was supplied.
    """
    report: dict[str, Any] = {
        "success": True,
        "status": "provider_activation_diagnostics_complete",
        "provider_count": 0,
        "activated_count": 0,
        "usable_count": 0,
        "providers": [],
        "issues": [],
        "recommendations": [],
        "routing_policy_compatible": None,
    }

    # --- Handle empty / malformed providers input ------------------------
    if providers is None:
        report["issues"].append("providers_config_missing")
        report["recommendations"].append(
            "Provide a 'providers' mapping with provider configuration entries."
        )
        return report

    if not _is_dict(providers):
        report["issues"].append("providers_config_not_dict")
        report["recommendations"].append(
            "The 'providers' configuration should be a dictionary keyed by provider id."
        )
        return report

    if len(providers) == 0:
        report["issues"].append("providers_config_empty")
        report["recommendations"].append(
            "Add at least one provider configuration entry."
        )
        return report

    aggregate_issues: list[str] = []
    aggregate_recommendations: list[str] = []

    for provider_id, provider_cfg in providers.items():
        provider_id_str = str(provider_id)
        diag = _diagnose_single_provider(provider_id_str, provider_cfg)
        report["providers"].append(diag)
        if diag["activated"]:
            report["activated_count"] += 1
        if diag.get("usable"):
            report["usable_count"] += 1
        aggregate_issues.extend(diag["issues"])
        aggregate_recommendations.extend(diag["recommendations"])

    report["provider_count"] = len(report["providers"])

    # Deduplicate while preserving order.
    seen: set[str] = set()
    unique_issues: list[str] = []
    for item in aggregate_issues:
        if item not in seen:
            seen.add(item)
            unique_issues.append(item)
    report["issues"] = unique_issues

    seen_rec: set[str] = set()
    unique_recs: list[str] = []
    for item in aggregate_recommendations:
        if item not in seen_rec:
            seen_rec.add(item)
            unique_recs.append(item)
    report["recommendations"] = unique_recs

    # --- Routing policy compatibility check -------------------------------
    if routing_policy is not None:
        if not _is_dict(routing_policy):
            report["issues"].append("routing_policy_not_dict")
            report["recommendations"].append(
                "Provide routing policy as a dictionary."
            )
            report["routing_policy_compatible"] = False
        else:
            primary = routing_policy.get("primary_provider")
            fallback = routing_policy.get("fallback_provider")

            provider_ids = {p["provider_id"] for p in report["providers"]}
            usable_ids = {
                p["provider_id"] for p in report["providers"] if p.get("usable")
            }

            compatible = True
            if primary is not None and str(primary) not in provider_ids:
                report["issues"].append("routing_policy_primary_provider_unknown")
                report["recommendations"].append(
                    "Routing policy references an unknown primary provider."
                )
                compatible = False
            elif primary is not None and str(primary) not in usable_ids:
                report["issues"].append("routing_policy_primary_provider_not_usable")
                report["recommendations"].append(
                    "Routing policy primary provider is not currently usable."
                )
                compatible = False

            if fallback is not None and str(fallback) not in provider_ids:
                report["issues"].append("routing_policy_fallback_provider_unknown")
                report["recommendations"].append(
                    "Routing policy references an unknown fallback provider."
                )
                compatible = False
            elif fallback is not None and str(fallback) not in usable_ids:
                report["issues"].append("routing_policy_fallback_provider_not_usable")
                report["recommendations"].append(
                    "Routing policy fallback provider is not currently usable."
                )
                compatible = False

            report["routing_policy_compatible"] = compatible

    return report
