"""Core implementation for provider activation diagnostics.

The public entry point is :func:`diagnose_provider_activation`, which accepts
optional provider health, provenance, and routing-plan payloads and returns a
structured diagnostic report. All inputs are validated defensively; malformed
or empty inputs are handled safely and never raise.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _is_dict(value: Any) -> bool:
    return isinstance(value, dict)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if isinstance(value, bool):
            return int(value)
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    return default


def _safe_str(value: Any, default: str = "") -> str:
    if isinstance(value, str):
        return value
    return default


def _coerce_dict(value: Any) -> Dict[str, Any]:
    if _is_dict(value):
        return value
    return {}


def _coerce_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    return []


def _summarize_provider_block(block: Any, name: str) -> Dict[str, Any]:
    block = _coerce_dict(block)
    return {
        "provider": _safe_str(block.get("provider"), name),
        "configured": _safe_bool(block.get("configured")),
        "usable": _safe_bool(block.get("usable"), _safe_bool(block.get("reachable"))),
        "reachable": _safe_bool(block.get("reachable")),
        "status": block.get("status"),
        "note": _safe_str(block.get("note")),
    }


def _analyze_provenance(events: Any) -> Dict[str, Any]:
    events = _coerce_list(events)
    counts: Dict[str, int] = {}
    failures = 0
    confidences: List[float] = []

    for event in events:
        if not _is_dict(event):
            continue
        provider = _safe_str(event.get("provider_used"), "unknown")
        counts[provider] = counts.get(provider, 0) + 1
        if event.get("primary_failure"):
            failures += 1
        confidence = event.get("confidence")
        try:
            if confidence is not None:
                confidences.append(float(confidence))
        except (TypeError, ValueError):
            continue

    avg_confidence = (
        round(sum(confidences) / len(confidences), 4) if confidences else None
    )

    return {
        "event_count": len(events),
        "provider_counts": counts,
        "primary_failures": failures,
        "average_confidence": avg_confidence,
    }


def _analyze_routing_plan(plan: Any) -> Dict[str, Any]:
    plan = _coerce_dict(plan)
    routes = _coerce_list(plan.get("routes"))
    primary = 0
    fallback = 0
    local_available = 0

    for route in routes:
        if not _is_dict(route):
            continue
        if _safe_str(route.get("primary_provider")):
            primary += 1
        if _safe_str(route.get("fallback_provider")):
            fallback += 1
        if _safe_bool(route.get("local_available")):
            local_available += 1

    return {
        "route_count": _safe_int(plan.get("route_count"), len(routes)),
        "primary_provider_routes": primary,
        "fallback_provider_routes": fallback,
        "local_available_routes": local_available,
    }


def _build_issues(
    health: Dict[str, Any],
    provenance_summary: Dict[str, Any],
    routing_summary: Dict[str, Any],
) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []

    primary = _summarize_provider_block(health.get("primary"), "primary")
    fallback = _summarize_provider_block(health.get("fallback"), "fallback")

    if not primary["configured"]:
        issues.append({
            "code": "primary_not_configured",
            "severity": "high",
            "message": "Primary provider is not configured.",
            "provider": primary["provider"],
        })

    if not primary["usable"]:
        issues.append({
            "code": "primary_not_usable",
            "severity": "high",
            "message": "Primary provider is configured but not usable.",
            "provider": primary["provider"],
        })

    if not fallback["configured"]:
        issues.append({
            "code": "fallback_not_configured",
            "severity": "medium",
            "message": "Fallback provider is not configured.",
            "provider": fallback["provider"],
        })

    if fallback["configured"] and not fallback["reachable"]:
        issues.append({
            "code": "fallback_not_reachable",
            "severity": "medium",
            "message": "Fallback provider is configured but not reachable.",
            "provider": fallback["provider"],
        })

    if not _safe_bool(health.get("healthy")):
        issues.append({
            "code": "overall_unhealthy",
            "severity": "high",
            "message": "Overall provider health is reported as unhealthy.",
        })

    if provenance_summary["event_count"] > 0:
        failure_rate = (
            provenance_summary["primary_failures"]
            / provenance_summary["event_count"]
        )
        if failure_rate >= 0.25:
            issues.append({
                "code": "elevated_primary_failure_rate",
                "severity": "medium",
                "message": "Primary failure rate in provenance log is elevated.",
                "failure_rate": round(failure_rate, 4),
            })

    if (
        routing_summary["route_count"] > 0
        and routing_summary["local_available_routes"] == 0
    ):
        issues.append({
            "code": "no_local_fallback_available",
            "severity": "low",
            "message": "Routing plan has routes but none report local fallback availability.",
        })

    return issues


def _build_recommendations(issues: List[Dict[str, Any]]) -> List[str]:
    codes = {issue.get("code") for issue in issues}
    recs: List[str] = []

    if "primary_not_configured" in codes:
        recs.append("Configure the primary provider credentials before activation.")
    if "primary_not_usable" in codes:
        recs.append("Validate primary provider usability before routing work to it.")
    if "fallback_not_configured" in codes:
        recs.append("Configure a fallback provider for resilience.")
    if "fallback_not_reachable" in codes:
        recs.append("Check fallback provider connectivity and health endpoint.")
    if "overall_unhealthy" in codes:
        recs.append("Resolve provider health issues before enabling automated routing.")
    if "elevated_primary_failure_rate" in codes:
        recs.append("Review recent primary provider failures and consider temporary fallback bias.")
    if "no_local_fallback_available" in codes:
        recs.append("Ensure at least one route has a reachable local fallback.")
    if not recs:
        recs.append("Provider activation diagnostics found no actionable issues.")
    return recs


def diagnose_provider_activation(
    health_report: Optional[Dict[str, Any]] = None,
    provenance_log: Optional[Dict[str, Any]] = None,
    routing_plan: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Return structured diagnostics for provider activation state.

    This function performs no network, financial, or external actions. It
    inspects the provided payloads and returns a deterministic diagnostic
    report. Empty or malformed inputs are handled safely.

    Parameters
    ----------
    health_report:
        Optional provider health report payload.
    provenance_log:
        Optional AI provenance log payload.
    routing_plan:
        Optional AI task routing plan payload.

    Returns
    -------
    dict
        Structured diagnostic report with keys: ``success``, ``status``,
        ``providers``, ``provenance``, ``routing``, ``issues``,
        ``recommendations``, and ``external_actions_performed``.
    """
    health = _coerce_dict(health_report)
    provenance = _coerce_dict(provenance_log)
    routing = _coerce_dict(routing_plan)

    primary = _summarize_provider_block(health.get("primary"), "primary")
    fallback = _summarize_provider_block(health.get("fallback"), "fallback")

    provenance_summary = _analyze_provenance(provenance.get("events"))
    routing_summary = _analyze_routing_plan(routing)

    issues = _build_issues(health, provenance_summary, routing_summary)
    recommendations = _build_recommendations(issues)

    activation_ready = (
        primary["configured"]
        and primary["usable"]
        and (fallback["configured"] and fallback["reachable"] or fallback["configured"])
        and not any(i["severity"] == "high" for i in issues)
    )

    return {
        "success": True,
        "status": "provider_activation_diagnostics_complete",
        "activation_ready": bool(activation_ready),
        "providers": {
            "primary": primary,
            "fallback": fallback,
            "overall_healthy": _safe_bool(health.get("healthy")),
        },
        "provenance": provenance_summary,
        "routing": routing_summary,
        "issues": issues,
        "issue_count": len(issues),
        "recommendations": recommendations,
        "external_actions_performed": False,
        "network_access_performed": False,
        "financial_actions_performed": False,
    }
