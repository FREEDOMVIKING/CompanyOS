"""Tests for generated_provider_activation_diagnostics."""

from __future__ import annotations

import pytest

from generated_provider_activation_diagnostics import (
    ProviderActivationDiagnostics,
    diagnose_provider_activation,
)


def test_empty_input_returns_empty_diagnostics():
    result = diagnose_provider_activation(None)
    assert isinstance(result, ProviderActivationDiagnostics)
    d = result.to_dict()
    assert d["summary"]["total_providers"] == 0
    assert d["summary"]["activation_ready_count"] == 0
    assert d["summary"]["usable_for_routing_count"] == 0
    assert d["providers"] == []
    assert d["issues"] == []
    assert isinstance(d["recommendations"], list)
    assert len(d["recommendations"]) == 1


def test_empty_list_returns_empty_diagnostics():
    result = diagnose_provider_activation([])
    d = result.to_dict()
    assert d["summary"]["total_providers"] == 0
    assert d["summary"]["healthy"] is False


def test_single_provider_mapping_is_accepted():
    provider = {
        "provider": "openai",
        "configured": True,
        "enabled": True,
        "api_key": "sk-test",
        "reachable": True,
        "healthy": True,
    }
    result = diagnose_provider_activation(provider)
    d = result.to_dict()
    assert d["summary"]["total_providers"] == 1
    assert d["summary"]["activation_ready_count"] == 1
    assert d["summary"]["usable_for_routing_count"] == 1
    assert d["summary"]["healthy"] is True
    assert d["providers"][0]["provider"] == "openai"
    assert d["providers"][0]["activation_ready"] is True
    assert d["providers"][0]["usable_for_routing"] is True
    assert d["providers"][0]["issues"] == []


def test_multiple_providers():
    providers = [
        {
            "provider": "openai",
            "configured": True,
            "enabled": True,
            "api_key": "sk-test",
            "reachable": True,
            "healthy": True,
        },
        {
            "provider": "local_llama",
            "configured": True,
            "enabled": True,
            "token": "abc",
            "reachable": False,
            "healthy": False,
        },
    ]
    result = diagnose_provider_activation(providers)
    d = result.to_dict()
    assert d["summary"]["total_providers"] == 2
    assert d["summary"]["activation_ready_count"] == 2
    assert d["summary"]["usable_for_routing_count"] == 1
    assert d["summary"]["healthy"] is False
    # local_llama is activation-ready but not usable for routing
    local = [p for p in d["providers"] if p["provider"] == "local_llama"][0]
    assert local["activation_ready"] is True
    assert local["usable_for_routing"] is False
    assert any(i["code"] == "activation_ready_but_unreachable" for i in local["issues"])


def test_missing_credentials_flagged():
    providers = [
        {
            "provider": "openai",
            "configured": True,
            "enabled": True,
            "reachable": True,
            "healthy": True,
        }
    ]
    result = diagnose_provider_activation(providers)
    d = result.to_dict()
    assert d["summary"]["activation_ready_count"] == 0
    assert d["summary"]["high_severity_issue_count"] >= 1
    assert any(i["code"] == "missing_credentials" for i in d["issues"])


def test_not_configured_flagged():
    providers = [
        {
            "provider": "openai",
            "configured": False,
            "enabled": True,
            "api_key": "sk-test",
        }
    ]
    result = diagnose_provider_activation(providers)
    d = result.to_dict()
    assert d["summary"]["activation_ready_count"] == 0
    assert any(i["code"] == "not_configured" for i in d["issues"])


def test_not_enabled_flagged():
    providers = [
        {
            "provider": "openai",
            "configured": True,
            "enabled": False,
            "api_key": "sk-test",
        }
    ]
    result = diagnose_provider_activation(providers)
    d = result.to_dict()
    assert d["summary"]["activation_ready_count"] == 0
    assert any(i["code"] == "not_enabled" for i in d["issues"])


def test_malformed_provider_entry():
    providers = ["not-a-dict", 42, None]
    result = diagnose_provider_activation(providers)
    d = result.to_dict()
    assert d["summary"]["total_providers"] == 3
    assert d["summary"]["malformed_count"] == 3
    assert d["summary"]["activation_ready_count"] == 0
    for p in d["providers"]:
        assert p["malformed"] is True
    assert any(i["code"] == "malformed_provider_entry" for i in d["issues"])


def test_unnamed_provider_gets_default_name():
    providers = [
        {
            "configured": True,
            "enabled": True,
            "api_key": "sk-test",
        }
    ]
    result = diagnose_provider_activation(providers)
    d = result.to_dict()
    assert d["providers"][0]["provider"] == "unnamed_provider_0"


def test_string_truthy_values():
    providers = [
        {
            "provider": "openai",
            "configured": "true",
            "enabled": "yes",
            "api_key": "sk-test",
            "reachable": "on",
            "healthy": "enabled",
        }
    ]
    result = diagnose_provider_activation(providers)
    d = result.to_dict()
    assert d["summary"]["activation_ready_count"] == 1
    assert d["summary"]["usable_for_routing_count"] == 1


def test_include_recommendations_false():
    providers = [
        {
            "provider": "openai",
            "configured": True,
            "enabled": True,
            "api_key": "sk-test",
            "reachable": True,
            "healthy": True,
        }
    ]
    result = diagnose_provider_activation(providers, include_recommendations=False)
    d = result.to_dict()
    assert d["recommendations"] == []


def test_single_usable_provider_recommendation():
    providers = [
        {
            "provider": "openai",
            "configured": True,
            "enabled": True,
            "api_key": "sk-test",
            "reachable": True,
            "healthy": True,
        }
    ]
    result = diagnose_provider_activation(providers)
    d = result.to_dict()
    assert any("fallback" in r.lower() for r in d["recommendations"])


def test_healthy_recommendation_when_all_good():
    providers = [
        {
            "provider": "openai",
            "configured": True,
            "enabled": True,
            "api_key": "sk-test",
            "reachable": True,
            "healthy": True,
        },
        {
            "provider": "local_llama",
            "configured": True,
            "enabled": True,
            "token": "abc",
            "reachable": True,
            "healthy": True,
        },
    ]
    result = diagnose_provider_activation(providers)
    d = result.to_dict()
    assert d["summary"]["healthy"] is True
    assert any("no action required" in r.lower() for r in d["recommendations"])


def test_to_dict_returns_plain_types():
    result = diagnose_provider_activation(
        {"provider": "openai", "configured": True, "enabled": True, "api_key": "k"}
    )
    d = result.to_dict()
    assert isinstance(d, dict)
    assert isinstance(d["summary"], dict)
    assert isinstance(d["providers"], list)
    assert isinstance(d["issues"], list)
    assert isinstance(d["recommendations"], list)


def test_no_external_side_effects():
    """Ensure the function does not touch network or filesystem."""
    providers = [
        {
            "provider": "openai",
            "configured": True,
            "enabled": True,
            "api_key": "sk-test",
            "reachable": True,
            "healthy": True,
        }
    ]
    # Should complete without any external calls.
    result = diagnose_provider_activation(providers)
    assert result.summary["total_providers"] == 1


def test_mixed_valid_and_malformed():
    providers = [
        {
            "provider": "openai",
            "configured": True,
            "enabled": True,
            "api_key": "sk-test",
            "reachable": True,
            "healthy": True,
        },
        "malformed-entry",
        {
            "provider": "local_llama",
            "configured": True,
            "enabled": False,
            "token": "abc",
        },
    ]
    result = diagnose_provider_activation(providers)
    d = result.to_dict()
    assert d["summary"]["total_providers"] == 3
    assert d["summary"]["malformed_count"] == 1
    assert d["summary"]["activation_ready_count"] == 1
    assert d["summary"]["usable_for_routing_count"] == 1


def test_activated_field_does_not_imply_ready():
    providers = [
        {
            "provider": "openai",
            "configured": False,
            "enabled": False,
            "activated": True,
        }
    ]
    result = diagnose_provider_activation(providers)
    d = result.to_dict()
    assert d["providers"][0]["activated"] is True
    assert d["providers"][0]["activation_ready"] is False


def test_credential_variants():
    providers = [
        {"provider": "p1", "configured": True, "enabled": True, "apiKey": "k"},
        {"provider": "p2", "configured": True, "enabled": True, "auth_token": "k"},
        {"provider": "p3", "configured": True, "enabled": True, "credentials": {"a": 1}},
        {"provider": "p4", "configured": True, "enabled": True, "secret": ["x"]},
    ]
    result = diagnose_provider_activation(providers)
    d = result.to_dict()
    assert d["summary"]["activation_ready_count"] == 4


def test_empty_credential_values_not_counted():
    providers = [
        {"provider": "p1", "configured": True, "enabled": True, "api_key": ""},
        {"provider": "p2", "configured": True, "enabled": True, "api_key": "   "},
    ]
    result = diagnose_provider_activation(providers)
    d = result.to_dict()
    assert d["summary"]["activation_ready_count"] == 0
    assert all(i["code"] == "missing_credentials" for i in d["issues"])
