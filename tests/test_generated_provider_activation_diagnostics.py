"""Tests for generated_provider_activation_diagnostics."""

from __future__ import annotations

import pytest

from generated_provider_activation_diagnostics import (
    diagnose_provider_activation,
    ActivationDiagnosticsResult,
)


def test_returns_structured_result_type():
    result = diagnose_provider_activation({}, {})
    assert isinstance(result, ActivationDiagnosticsResult)
    assert result.status == "provider_activation_diagnostics_complete"


def test_to_dict_roundtrip():
    result = diagnose_provider_activation({}, {})
    payload = result.to_dict()
    assert isinstance(payload, dict)
    assert set(payload.keys()) == {
        "success",
        "status",
        "summary",
        "providers",
        "recommendations",
        "errors",
    }


def test_empty_inputs_use_supported_providers():
    result = diagnose_provider_activation()
    names = {p["provider"] for p in result.providers}
    assert names == {"openai", "local_llama"}
    assert result.summary["provider_count"] == 2


def test_none_inputs_are_safe():
    result = diagnose_provider_activation(None, None)
    assert result.success is False
    assert result.providers
    assert result.summary["overall_state"] == "inactive"


def test_malformed_config_and_health_recorded_as_errors():
    result = diagnose_provider_activation("not a dict", 42)
    assert "provider_config was not a mapping; treated as empty." in result.errors
    assert "provider_health was not a mapping; treated as empty." in result.errors


def test_fully_activated_primary_provider():
    config = {
        "openai": {
            "configured": True,
            "enabled": True,
            "api_key_present": True,
            "base_url": "https://api.openai.com",
            "timeout_seconds": 20,
        }
    }
    health = {
        "openai": {
            "usable": True,
            "reachable": True,
            "status": "ok",
        }
    }
    result = diagnose_provider_activation(config, health)
    assert result.success is True
    assert result.summary["overall_state"] == "operational"
    assert result.summary["routing_recommendation"] == "primary_available"
    assert result.summary["primary_ready"] is True
    openai = next(p for p in result.providers if p["provider"] == "openai")
    assert openai["activation_state"] == "activated"
    assert openai["issues"] == []


def test_fallback_only_when_primary_missing_key():
    config = {
        "openai": {
            "configured": True,
            "enabled": True,
            "api_key_present": False,
            "timeout_seconds": 20,
        },
        "local_llama": {
            "configured": True,
            "enabled": True,
            "base_url": "http://127.0.0.1:8080",
            "timeout_seconds": 30,
        },
    }
    health = {
        "openai": {"usable": False, "reachable": False},
        "local_llama": {"usable": True, "reachable": True, "status": "ok"},
    }
    result = diagnose_provider_activation(config, health)
    assert result.success is False
    assert result.summary["routing_recommendation"] == "fallback_only"
    assert result.summary["fallback_ready"] is True
    openai = next(p for p in result.providers if p["provider"] == "openai")
    assert openai["activation_state"] == "activation_blocked"
    codes = {i["code"] for i in openai["issues"]}
    assert "missing_api_key" in codes
    assert "configured_but_not_usable" in codes


def test_pending_activation_state():
    config = {
        "openai": {
            "configured": True,
            "enabled": True,
            "api_key_present": True,
            "timeout_seconds": 20,
        }
    }
    health = {"openai": {"usable": False, "reachable": False}}
    result = diagnose_provider_activation(config, health)
    openai = next(p for p in result.providers if p["provider"] == "openai")
    assert openai["activation_state"] == "pending_activation"
    assert result.summary["overall_state"] == "pending"
    assert result.summary["routing_recommendation"] == "awaiting_primary_activation"


def test_disabled_provider():
    config = {
        "openai": {
            "configured": True,
            "enabled": False,
            "api_key_present": True,
            "timeout_seconds": 20,
        }
    }
    health = {"openai": {"usable": True, "reachable": True}}
    result = diagnose_provider_activation(config, health)
    openai = next(p for p in result.providers if p["provider"] == "openai")
    assert openai["activation_state"] == "disabled"
    assert any(w["code"] == "provider_disabled" for w in openai["warnings"])


def test_local_llama_not_reachable_issue():
    config = {
        "local_llama": {
            "configured": True,
            "enabled": True,
            "base_url": "http://127.0.0.1:8080",
            "timeout_seconds": 30,
        }
    }
    health = {"local_llama": {"usable": True, "reachable": False}}
    result = diagnose_provider_activation(config, health)
    local = next(p for p in result.providers if p["provider"] == "local_llama")
    codes = {i["code"] for i in local["issues"]}
    assert "not_reachable" in codes


def test_missing_base_url_warning_for_local_llama():
    config = {
        "local_llama": {
            "configured": True,
            "enabled": True,
            "timeout_seconds": 30,
        }
    }
    health = {"local_llama": {"usable": True, "reachable": True}}
    result = diagnose_provider_activation(config, health)
    local = next(p for p in result.providers if p["provider"] == "local_llama")
    assert any(w["code"] == "missing_base_url" for w in local["warnings"])


def test_invalid_timeout_warning():
    config = {
        "openai": {
            "configured": True,
            "enabled": True,
            "api_key_present": True,
            "timeout_seconds": 0,
        }
    }
    health = {"openai": {"usable": True, "reachable": True}}
    result = diagnose_provider_activation(config, health)
    openai = next(p for p in result.providers if p["provider"] == "openai")
    assert any(w["code"] == "invalid_timeout" for w in openai["warnings"])


def test_explicit_providers_list_respected():
    config = {
        "openai": {"configured": True, "enabled": True, "api_key_present": True, "timeout_seconds": 10},
        "local_llama": {"configured": True, "enabled": True, "base_url": "http://x", "timeout_seconds": 10},
    }
    health = {
        "openai": {"usable": True, "reachable": True},
        "local_llama": {"usable": True, "reachable": True},
    }
    result = diagnose_provider_activation(config, health, providers=["openai"])
    assert {p["provider"] for p in result.providers} == {"openai"}
    assert result.summary["provider_count"] == 1


def test_recommendations_include_issues():
    config = {"openai": {"configured": True, "enabled": True, "api_key_present": False}}
    health = {"openai": {"usable": False}}
    result = diagnose_provider_activation(config, health)
    joined = "\n".join(result.recommendations)
    assert "missing_api_key" in joined


def test_no_issues_yields_clean_recommendation():
    config = {
        "openai": {
            "configured": True,
            "enabled": True,
            "api_key_present": True,
            "timeout_seconds": 20,
        }
    }
    health = {"openai": {"usable": True, "reachable": True, "status": "ok"}}
    result = diagnose_provider_activation(config, health)
    assert result.recommendations == [
        "Provider activation diagnostics completed with no actions required."
    ]


def test_malformed_provider_entry_treated_safely():
    config = {"openai": "not a dict"}
    health = {"openai": 123}
    result = diagnose_provider_activation(config, health)
    openai = next(p for p in result.providers if p["provider"] == "openai")
    codes = {i["code"] for i in openai["issues"]}
    assert "malformed_config" in codes
    assert "malformed_health" in codes
    assert openai["activation_state"] == "activation_blocked"


def test_empty_explicit_providers_list():
    result = diagnose_provider_activation({}, {}, providers=[])
    assert result.providers == []
    assert "No providers supplied for diagnostics." in result.errors
    assert result.success is False


def test_recent_error_warning():
    config = {
        "openai": {
            "configured": True,
            "enabled": True,
            "api_key_present": True,
            "timeout_seconds": 20,
        }
    }
    health = {"openai": {"usable": True, "reachable": True, "last_error": "timeout"}}
    result = diagnose_provider_activation(config, health)
    openai = next(p for p in result.providers if p["provider"] == "openai")
    assert any(w["code"] == "recent_error" for w in openai["warnings"])


def test_summary_counts_consistent():
    config = {
        "openai": {"configured": True, "enabled": True, "api_key_present": True, "timeout_seconds": 10},
        "local_llama": {"configured": True, "enabled": False, "base_url": "http://x", "timeout_seconds": 10},
    }
    health = {
        "openai": {"usable": True, "reachable": True},
        "local_llama": {"usable": True, "reachable": True},
    }
    result = diagnose_provider_activation(config, health)
    s = result.summary
    assert s["provider_count"] == 2
    assert s["activated_count"] == 1
    assert s["disabled_count"] == 1
    assert s["issue_count"] == 0
    assert s["overall_state"] == "operational"


def test_degraded_state_when_blocked():
    config = {
        "openai": {"configured": True, "enabled": True, "api_key_present": False},
        "local_llama": {"configured": False, "enabled": True},
    }
    health = {"openai": {"usable": False}, "local_llama": {"usable": False}}
    result = diagnose_provider_activation(config, health)
    assert result.summary["overall_state"] == "degraded"
    assert result.summary["blocked_count"] >= 1


def test_no_external_actions_flag():
    result = diagnose_provider_activation({}, {})
    # Ensure function is pure and does not attempt external side effects.
    assert isinstance(result, ActivationDiagnosticsResult)
    assert result.status.startswith("provider_activation_diagnostics")


def test_not_configured_without_blocking_issues():
    """A provider with no config and no health should be not_configured, not blocked."""
    result = diagnose_provider_activation({}, {}, providers=["openai"])
    openai = next(p for p in result.providers if p["provider"] == "openai")
    assert openai["activation_state"] == "not_configured"
    assert openai["issues"] == []


def test_malformed_config_blocks_before_not_configured():
    """Malformed config should produce activation_blocked, not not_configured."""
    config = {"openai": ["bad"]}
    health = {"openai": {"usable": True, "reachable": True}}
    result = diagnose_provider_activation(config, health)
    openai = next(p for p in result.providers if p["provider"] == "openai")
    assert openai["activation_state"] == "activation_blocked"
    codes = {i["code"] for i in openai["issues"]}
    assert "malformed_config" in codes


def test_malformed_health_blocks_activation():
    """Malformed health alone should block activation even if config is valid."""
    config = {"openai": {"configured": True, "enabled": True, "api_key_present": True, "timeout_seconds": 20}}
    health = {"openai": "bad"}
    result = diagnose_provider_activation(config, health)
    openai = next(p for p in result.providers if p["provider"] == "openai")
    assert openai["activation_state"] == "activation_blocked"
    codes = {i["code"] for i in openai["issues"]}
    assert "malformed_health" in codes
