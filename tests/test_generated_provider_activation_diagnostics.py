from __future__ import annotations

import pytest

from generated_provider_activation_diagnostics import diagnose_provider_activation
from generated_provider_activation_diagnostics.core import (
    diagnose_provider_activation as core_diagnose,
)


def test_public_function_matches_core_function():
    assert diagnose_provider_activation is core_diagnose


def test_empty_input_returns_safe_report():
    result = diagnose_provider_activation()
    assert result["success"] is True
    assert result["status"] == "provider_activation_diagnostics_complete"
    assert result["providers"] == []
    assert result["healthy"] is False
    assert result["primary_active"] is False
    assert result["fallback_active"] is False
    assert result["issue_count"] == 1
    assert result["external_actions_taken"] is False
    assert "generated_at" in result
    assert isinstance(result["recommendations"], list)


def test_none_input_returns_safe_report():
    result = diagnose_provider_activation(None)
    assert result["success"] is True
    assert result["providers"] == []
    assert result["issue_count"] == 1


def test_malformed_non_dict_input():
    result = diagnose_provider_activation("not-a-dict")
    assert result["success"] is True
    assert result["providers"] == []
    assert result["issue_count"] == 1
    assert any("malformed" in r.lower() for r in result["recommendations"])


def test_malformed_list_input():
    result = diagnose_provider_activation(["primary", "fallback"])
    assert result["success"] is True
    assert result["providers"] == []
    assert result["issue_count"] == 1


def test_fully_healthy_providers():
    report = {
        "primary": {
            "provider": "openai",
            "configured": True,
            "usable": True,
        },
        "fallback": {
            "provider": "local_llama",
            "configured": True,
            "usable": True,
            "reachable": True,
        },
        "healthy": True,
        "routing_policy": "primary_then_fallback",
    }
    result = diagnose_provider_activation(report)
    assert result["healthy"] is True
    assert result["primary_active"] is True
    assert result["fallback_active"] is True
    assert result["issue_count"] == 0
    assert result["routing_policy"] == "primary_then_fallback"
    assert len(result["providers"]) == 2
    assert result["providers"][0]["valid"] is True
    assert result["providers"][1]["valid"] is True


def test_primary_not_configured():
    report = {
        "primary": {"provider": "openai", "configured": False, "usable": False},
        "fallback": {
            "provider": "local_llama",
            "configured": True,
            "usable": True,
            "reachable": True,
        },
        "routing_policy": "primary_then_fallback",
    }
    result = diagnose_provider_activation(report)
    assert result["primary_active"] is False
    assert result["fallback_active"] is True
    assert result["healthy"] is True
    assert "not_configured" in result["providers"][0]["issues"]
    assert result["issue_count"] >= 1


def test_configured_but_not_usable():
    report = {
        "primary": {
            "provider": "openai",
            "configured": True,
            "usable": False,
        },
        "fallback": {
            "provider": "local_llama",
            "configured": True,
            "usable": False,
            "reachable": False,
        },
    }
    result = diagnose_provider_activation(report)
    assert result["primary_active"] is False
    assert result["fallback_active"] is False
    assert result["healthy"] is False
    assert "configured_but_not_usable" in result["providers"][0]["issues"]
    assert "configured_but_not_usable" in result["providers"][1]["issues"]
    assert "not_reachable" in result["providers"][1]["issues"]


def test_missing_primary_and_fallback():
    report = {"healthy": True}
    result = diagnose_provider_activation(report)
    assert result["primary_active"] is False
    assert result["fallback_active"] is False
    assert result["healthy"] is False
    assert "missing_primary_provider" in result["recommendations"]
    assert "missing_fallback_provider" in result["recommendations"]
    assert "declared_healthy_but_no_valid_provider" in result["recommendations"]


def test_malformed_provider_entry():
    report = {
        "primary": "broken",
        "fallback": 123,
    }
    result = diagnose_provider_activation(report)
    assert len(result["providers"]) == 2
    for entry in result["providers"]:
        assert entry["valid"] is False
        assert "malformed_provider_entry" in entry["issues"]


def test_routing_policy_override():
    report = {
        "primary": {"provider": "openai", "configured": True, "usable": True},
        "fallback": {
            "provider": "local_llama",
            "configured": True,
            "usable": True,
            "reachable": True,
        },
        "routing_policy": "original_policy",
    }
    result = diagnose_provider_activation(report, routing_policy="override_policy")
    assert result["routing_policy"] == "override_policy"


def test_missing_routing_policy_flagged():
    report = {
        "primary": {"provider": "openai", "configured": True, "usable": True},
        "fallback": {
            "provider": "local_llama",
            "configured": True,
            "usable": True,
            "reachable": True,
        },
    }
    result = diagnose_provider_activation(report)
    assert result["routing_policy"] == ""
    assert "missing_routing_policy" in result["recommendations"]


def test_string_truthy_values_handled():
    report = {
        "primary": {
            "provider": "openai",
            "configured": "true",
            "usable": "yes",
        },
        "fallback": {
            "provider": "local_llama",
            "configured": "1",
            "usable": "on",
            "reachable": "true",
        },
        "routing_policy": "primary_then_fallback",
    }
    result = diagnose_provider_activation(report)
    assert result["primary_active"] is True
    assert result["fallback_active"] is True
    assert result["healthy"] is True


def test_no_external_actions_flag():
    result = diagnose_provider_activation({})
    assert result["external_actions_taken"] is False


def test_return_type_structure():
    result = diagnose_provider_activation(
        {
            "primary": {"provider": "openai", "configured": True, "usable": True},
            "fallback": {
                "provider": "local_llama",
                "configured": True,
                "usable": True,
                "reachable": True,
            },
            "routing_policy": "primary_then_fallback",
        }
    )
    assert isinstance(result, dict)
    expected_keys = {
        "generated_at",
        "success",
        "status",
        "providers",
        "healthy",
        "primary_active",
        "fallback_active",
        "issue_count",
        "recommendations",
        "routing_policy",
        "external_actions_taken",
    }
    assert expected_keys.issubset(result.keys())
    assert isinstance(result["providers"], list)
    assert isinstance(result["recommendations"], list)
    assert isinstance(result["issue_count"], int)


def test_only_primary_present():
    report = {
        "primary": {"provider": "openai", "configured": True, "usable": True},
        "routing_policy": "primary_only",
    }
    result = diagnose_provider_activation(report)
    assert result["primary_active"] is True
    assert result["fallback_active"] is False
    assert result["healthy"] is True
    assert "missing_fallback_provider" in result["recommendations"]


def test_only_fallback_present():
    report = {
        "fallback": {
            "provider": "local_llama",
            "configured": True,
            "usable": True,
            "reachable": True,
        },
        "routing_policy": "fallback_only",
    }
    result = diagnose_provider_activation(report)
    assert result["primary_active"] is False
    assert result["fallback_active"] is True
    assert result["healthy"] is True
    assert "missing_primary_provider" in result["recommendations"]


def test_reachable_none_when_absent():
    report = {
        "primary": {"provider": "openai", "configured": True, "usable": True},
        "fallback": {
            "provider": "local_llama",
            "configured": True,
            "usable": True,
        },
        "routing_policy": "primary_then_fallback",
    }
    result = diagnose_provider_activation(report)
    assert result["providers"][0]["reachable"] is None
    assert result["providers"][1]["reachable"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
