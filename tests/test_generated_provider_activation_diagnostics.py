from __future__ import annotations

import pytest

from generated_provider_activation_diagnostics import diagnose_provider_activation
from generated_provider_activation_diagnostics.core import (
    _coerce_providers,
    _evaluate_activation,
)


def test_empty_input_returns_safe_report():
    report = diagnose_provider_activation()
    assert report["provider_count"] == 0
    assert report["activated_count"] == 0
    assert report["healthy"] is False
    assert report["providers"] == []
    assert report["issues"] == []
    assert report["external_actions_performed"] is False
    assert report["network_access_performed"] is False


def test_none_input_returns_safe_report():
    report = diagnose_provider_activation(None)
    assert report["provider_count"] == 0
    assert report["healthy"] is False


def test_single_provider_mapping_accepted():
    provider = {
        "provider": "openai",
        "configured": True,
        "usable": True,
        "reachable": True,
        "enabled": True,
        "healthy": True,
    }
    report = diagnose_provider_activation(provider)
    assert report["provider_count"] == 1
    assert report["activated_count"] == 1
    assert report["healthy"] is True
    assert report["providers"][0]["activation_state"] == "activated"
    assert report["providers"][0]["issues"] == []


def test_multiple_providers():
    providers = [
        {
            "provider": "openai",
            "configured": True,
            "usable": True,
            "reachable": True,
            "enabled": True,
            "healthy": True,
        },
        {
            "provider": "local_llama",
            "configured": True,
            "usable": True,
            "reachable": False,
            "enabled": True,
            "healthy": True,
        },
    ]
    report = diagnose_provider_activation(providers)
    assert report["provider_count"] == 2
    assert report["activated_count"] == 2
    assert report["healthy"] is True
    states = {p["provider"]: p["activation_state"] for p in report["providers"]}
    assert states["openai"] == "activated"
    assert states["local_llama"] == "degraded"


def test_unconfigured_provider():
    providers = [{"provider": "missing_provider"}]
    report = diagnose_provider_activation(providers)
    assert report["provider_count"] == 1
    assert report["activated_count"] == 0
    assert report["healthy"] is False
    assert report["providers"][0]["activation_state"] == "unconfigured"
    assert "provider_not_configured" in report["providers"][0]["issues"]


def test_disabled_provider():
    providers = [
        {
            "provider": "openai",
            "configured": True,
            "enabled": False,
            "usable": True,
            "reachable": True,
            "healthy": True,
        }
    ]
    report = diagnose_provider_activation(providers)
    assert report["activated_count"] == 0
    assert report["providers"][0]["activation_state"] == "standby"
    assert "provider_disabled" in report["providers"][0]["issues"]


def test_partial_activation():
    providers = [
        {
            "provider": "openai",
            "configured": True,
            "enabled": True,
            "usable": True,
            "reachable": False,
            "healthy": False,
        }
    ]
    report = diagnose_provider_activation(providers)
    assert report["activated_count"] == 1
    assert report["providers"][0]["activation_state"] == "partial"
    assert "provider_not_reachable" in report["providers"][0]["issues"]
    assert "provider_unhealthy" in report["providers"][0]["issues"]


def test_inactive_provider():
    providers = [
        {
            "provider": "openai",
            "configured": True,
            "enabled": False,
            "usable": False,
            "reachable": False,
            "healthy": True,
        }
    ]
    report = diagnose_provider_activation(providers)
    assert report["activated_count"] == 0
    assert report["providers"][0]["activation_state"] == "standby"


def test_malformed_provider_missing_name():
    providers = [{"configured": True}]
    report = diagnose_provider_activation(providers)
    assert report["provider_count"] == 1
    assert report["providers"][0]["malformed"] is True
    assert report["providers"][0]["activation_state"] == "invalid"
    assert report["activated_count"] == 0


def test_malformed_provider_not_mapping():
    providers = ["not_a_dict", 42, None]
    report = diagnose_provider_activation(providers)
    assert report["provider_count"] == 3
    for entry in report["providers"]:
        assert entry["malformed"] is True
        assert entry["activation_state"] == "invalid"
    assert report["activated_count"] == 0


def test_completely_unexpected_input_type():
    report = diagnose_provider_activation(12345)
    assert report["provider_count"] == 1
    assert report["providers"][0]["malformed"] is True
    assert report["providers"][0]["provider"] == "malformed_input"


def test_string_input_treated_as_malformed():
    report = diagnose_provider_activation("openai")
    assert report["provider_count"] == 1
    assert report["providers"][0]["malformed"] is True


def test_routing_policy_string():
    report = diagnose_provider_activation(
        [{"provider": "openai", "configured": True, "usable": True, "reachable": True, "enabled": True, "healthy": True}],
        routing_policy="primary_then_fallback",
    )
    assert report["routing_policy"] == {"policy": "primary_then_fallback"}


def test_routing_policy_mapping():
    report = diagnose_provider_activation(
        [{"provider": "openai", "configured": True, "usable": True, "reachable": True, "enabled": True, "healthy": True}],
        routing_policy={"primary": "openai", "fallback": "local_llama"},
    )
    assert report["routing_policy"]["primary"] == "openai"


def test_routing_policy_malformed():
    report = diagnose_provider_activation(
        [{"provider": "openai", "configured": True, "usable": True, "reachable": True, "enabled": True, "healthy": True}],
        routing_policy=123,
    )
    assert report["routing_policy"]["malformed"] is True


def test_routing_policy_none():
    report = diagnose_provider_activation(
        [{"provider": "openai", "configured": True, "usable": True, "reachable": True, "enabled": True, "healthy": True}],
    )
    assert report["routing_policy"] is None


def test_aggregate_issues_populated():
    providers = [
        {"provider": "openai", "configured": True, "usable": True, "reachable": True, "enabled": True, "healthy": True},
        {"provider": "local_llama", "configured": False},
    ]
    report = diagnose_provider_activation(providers)
    assert len(report["issues"]) >= 1
    assert any("local_llama" in issue for issue in report["issues"])


def test_coerce_providers_empty():
    assert _coerce_providers(None) == []


def test_coerce_providers_single_mapping():
    result = _coerce_providers({"provider": "openai", "configured": True})
    assert len(result) == 1
    assert result[0]["provider"] == "openai"
    assert result[0]["malformed"] is False


def test_evaluate_activation_invalid():
    result = _evaluate_activation({"provider": "bad", "malformed": True, "error": "bad"})
    assert result["activation_state"] == "invalid"
    assert result["activated"] is False


def test_report_has_generated_at_timestamp():
    report = diagnose_provider_activation()
    assert "generated_at" in report
    assert isinstance(report["generated_at"], str)
    assert "T" in report["generated_at"]


def test_optional_fields_preserved():
    provider = {
        "provider": "openai",
        "configured": True,
        "usable": True,
        "reachable": True,
        "enabled": True,
        "healthy": True,
        "status": 200,
        "base_url": "https://api.example.com",
        "note": "primary provider",
    }
    report = diagnose_provider_activation(provider)
    entry = report["providers"][0]
    assert entry["status"] == 200
    assert entry["base_url"] == "https://api.example.com"
    assert entry["note"] == "primary provider"


def test_all_providers_activated_is_healthy():
    providers = [
        {"provider": "a", "configured": True, "usable": True, "reachable": True, "enabled": True, "healthy": True},
        {"provider": "b", "configured": True, "usable": True, "reachable": True, "enabled": True, "healthy": True},
    ]
    report = diagnose_provider_activation(providers)
    assert report["healthy"] is True


def test_one_unhealthy_makes_not_healthy_when_not_activated():
    providers = [
        {"provider": "a", "configured": True, "usable": True, "reachable": True, "enabled": True, "healthy": True},
        {"provider": "b", "configured": False},
    ]
    report = diagnose_provider_activation(providers)
    assert report["healthy"] is False
    assert report["activated_count"] == 1
