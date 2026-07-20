from __future__ import annotations

import pytest

from generated_provider_activation_diagnostics import diagnose_provider_activation
from generated_provider_activation_diagnostics.core import diagnose_provider_activation as core_diag


def test_public_function_is_reexported():
    assert diagnose_provider_activation is core_diag


def test_empty_inputs_are_safe():
    result = diagnose_provider_activation()
    assert result["success"] is True
    assert result["status"] == "provider_activation_diagnostics_complete"
    assert result["issue_count"] >= 1
    assert result["external_actions_performed"] is False
    assert result["network_access_performed"] is False
    assert result["financial_actions_performed"] is False
    assert isinstance(result["recommendations"], list)
    assert result["recommendations"]


def test_none_inputs_are_safe():
    result = diagnose_provider_activation(None, None, None)
    assert result["success"] is True
    assert result["activation_ready"] is False


def test_malformed_inputs_do_not_raise():
    result = diagnose_provider_activation(
        health_report="not a dict",
        provenance_log=123,
        routing_plan=["bad"],
    )
    assert result["success"] is True
    assert result["provenance"]["event_count"] == 0
    assert result["routing"]["route_count"] == 0


def test_healthy_providers_yield_activation_ready():
    health = {
        "healthy": True,
        "primary": {"provider": "openai", "configured": True, "usable": True},
        "fallback": {"provider": "local_llama", "configured": True, "reachable": True},
    }
    result = diagnose_provider_activation(health_report=health)
    assert result["activation_ready"] is True
    assert result["providers"]["primary"]["usable"] is True
    assert result["providers"]["fallback"]["reachable"] is True
    assert result["issue_count"] == 0


def test_unhealthy_overall_flag_creates_high_issue():
    health = {
        "healthy": False,
        "primary": {"provider": "openai", "configured": True, "usable": True},
        "fallback": {"provider": "local_llama", "configured": True, "reachable": True},
    }
    result = diagnose_provider_activation(health_report=health)
    codes = [i["code"] for i in result["issues"]]
    assert "overall_unhealthy" in codes
    assert result["activation_ready"] is False


def test_primary_not_configured():
    health = {
        "healthy": False,
        "primary": {"provider": "openai", "configured": False, "usable": False},
        "fallback": {"provider": "local_llama", "configured": True, "reachable": True},
    }
    result = diagnose_provider_activation(health_report=health)
    codes = [i["code"] for i in result["issues"]]
    assert "primary_not_configured" in codes
    assert "primary_not_usable" in codes
    assert result["activation_ready"] is False


def test_fallback_not_reachable():
    health = {
        "healthy": True,
        "primary": {"provider": "openai", "configured": True, "usable": True},
        "fallback": {"provider": "local_llama", "configured": True, "reachable": False},
    }
    result = diagnose_provider_activation(health_report=health)
    codes = [i["code"] for i in result["issues"]]
    assert "fallback_not_reachable" in codes


def test_provenance_failure_rate_analysis():
    health = {
        "healthy": True,
        "primary": {"provider": "openai", "configured": True, "usable": True},
        "fallback": {"provider": "local_llama", "configured": True, "reachable": True},
    }
    provenance = {
        "events": [
            {"provider_used": "openai_primary", "primary_failure": None, "confidence": 0.9},
            {"provider_used": "openai_primary", "primary_failure": "timeout", "confidence": 0.4},
            {"provider_used": "openai_primary", "primary_failure": "timeout", "confidence": 0.3},
            {"provider_used": "local_llama_fallback", "primary_failure": None, "confidence": 0.8},
        ]
    }
    result = diagnose_provider_activation(health_report=health, provenance_log=provenance)
    assert result["provenance"]["event_count"] == 4
    assert result["provenance"]["primary_failures"] == 2
    assert result["provenance"]["average_confidence"] is not None
    codes = [i["code"] for i in result["issues"]]
    assert "elevated_primary_failure_rate" in codes


def test_provenance_malformed_events_ignored():
    provenance = {"events": ["bad", 123, None, {"provider_used": "openai"}]}
    result = diagnose_provider_activation(provenance_log=provenance)
    assert result["provenance"]["event_count"] == 4
    assert result["provenance"]["provider_counts"].get("openai") == 1


def test_routing_plan_analysis():
    routing = {
        "route_count": 3,
        "routes": [
            {"primary_provider": "openai", "fallback_provider": "local_llama", "local_available": True},
            {"primary_provider": "openai", "fallback_provider": "local_llama", "local_available": False},
            {"primary_provider": "openai", "fallback_provider": "local_llama", "local_available": True},
        ],
    }
    result = diagnose_provider_activation(routing_plan=routing)
    assert result["routing"]["route_count"] == 3
    assert result["routing"]["primary_provider_routes"] == 3
    assert result["routing"]["fallback_provider_routes"] == 3
    assert result["routing"]["local_available_routes"] == 2


def test_routing_no_local_fallback_issue():
    routing = {
        "route_count": 2,
        "routes": [
            {"primary_provider": "openai", "fallback_provider": "local_llama", "local_available": False},
            {"primary_provider": "openai", "fallback_provider": "local_llama", "local_available": False},
        ],
    }
    result = diagnose_provider_activation(routing_plan=routing)
    codes = [i["code"] for i in result["issues"]]
    assert "no_local_fallback_available" in codes


def test_recommendations_match_issues():
    health = {
        "healthy": False,
        "primary": {"provider": "openai", "configured": False, "usable": False},
        "fallback": {"provider": "local_llama", "configured": False, "reachable": False},
    }
    result = diagnose_provider_activation(health_report=health)
    recs = " ".join(result["recommendations"])
    assert "primary" in recs.lower()
    assert "fallback" in recs.lower()


def test_return_structure_keys():
    result = diagnose_provider_activation()
    expected_keys = {
        "success",
        "status",
        "activation_ready",
        "providers",
        "provenance",
        "routing",
        "issues",
        "issue_count",
        "recommendations",
        "external_actions_performed",
        "network_access_performed",
        "financial_actions_performed",
    }
    assert expected_keys.issubset(result.keys())


def test_deterministic_output():
    health = {
        "healthy": True,
        "primary": {"provider": "openai", "configured": True, "usable": True},
        "fallback": {"provider": "local_llama", "configured": True, "reachable": True},
    }
    r1 = diagnose_provider_activation(health_report=health)
    r2 = diagnose_provider_activation(health_report=health)
    assert r1 == r2


def test_fallback_usable_defaults_from_reachable():
    health = {
        "healthy": True,
        "primary": {"provider": "openai", "configured": True, "usable": True},
        "fallback": {"provider": "local_llama", "configured": True, "reachable": True},
    }
    result = diagnose_provider_activation(health_report=health)
    assert result["providers"]["fallback"]["usable"] is True


def test_no_high_issues_when_ready():
    health = {
        "healthy": True,
        "primary": {"provider": "openai", "configured": True, "usable": True},
        "fallback": {"provider": "local_llama", "configured": True, "reachable": True},
    }
    result = diagnose_provider_activation(health_report=health)
    assert not any(i["severity"] == "high" for i in result["issues"])


def test_routing_malformed_routes_ignored():
    routing = {"routes": ["bad", 1, None, {"primary_provider": "openai"}]}
    result = diagnose_provider_activation(routing_plan=routing)
    assert result["routing"]["primary_provider_routes"] == 1


def test_confidence_non_numeric_ignored():
    provenance = {
        "events": [
            {"provider_used": "openai", "confidence": "high"},
            {"provider_used": "openai", "confidence": 0.8},
        ]
    }
    result = diagnose_provider_activation(provenance_log=provenance)
    assert result["provenance"]["average_confidence"] == 0.8


def test_status_string_present():
    result = diagnose_provider_activation()
    assert isinstance(result["status"], str)
    assert result["status"]


def test_issue_severities_valid():
    result = diagnose_provider_activation()
    for issue in result["issues"]:
        assert issue["severity"] in {"low", "medium", "high"}
        assert "code" in issue
        assert "message" in issue


def test_package_contract_importable():
    import generated_provider_activation_diagnostics as pkg
    assert hasattr(pkg, "diagnose_provider_activation")
    assert pkg.__all__ == ["diagnose_provider_activation"]
