#!/usr/bin/env python3
"""Tests for generated_provider_activation_diagnostics."""
from __future__ import annotations

import pytest

from generated_provider_activation_diagnostics import diagnose_provider_activation
from generated_provider_activation_diagnostics import core


def test_empty_input_returns_safe_report():
    result = diagnose_provider_activation()
    assert result["total_providers"] == 0
    assert result["activated_count"] == 0
    assert result["issue_count"] == 0
    assert result["diagnostics"] == []
    assert result["external_actions_performed"] is False
    assert result["network_access_performed"] is False
    assert "generated_at" in result


def test_none_input_returns_safe_report():
    result = diagnose_provider_activation(None)
    assert result["total_providers"] == 0
    assert result["healthy"] is False


def test_single_active_provider_dict():
    provider = {
        "provider": "openai",
        "status": "active",
        "configured": True,
        "has_credentials": True,
        "reachable": True,
    }
    result = diagnose_provider_activation(provider)
    assert result["total_providers"] == 1
    assert result["activated_count"] == 1
    assert result["ready_count"] == 1
    diag = result["diagnostics"][0]
    assert diag["provider"] == "openai"
    assert diag["activated"] is True
    assert diag["ready"] is True
    assert diag["issues"] == []


def test_active_without_credentials_not_activated():
    provider = {
        "provider": "openai",
        "status": "active",
        "configured": True,
        "has_credentials": False,
        "reachable": True,
    }
    result = diagnose_provider_activation(provider)
    assert result["activated_count"] == 0
    diag = result["diagnostics"][0]
    assert "active_without_credentials" in diag["issues"]


def test_active_without_credentials_activated_when_not_required():
    provider = {
        "provider": "openai",
        "status": "active",
        "configured": True,
        "has_credentials": False,
        "reachable": True,
    }
    result = diagnose_provider_activation(provider, require_credentials=False)
    assert result["activated_count"] == 1
    diag = result["diagnostics"][0]
    assert diag["activated"] is True


def test_require_reachable_flag():
    provider = {
        "provider": "local_llama",
        "status": "active",
        "configured": True,
        "has_credentials": True,
        "reachable": False,
    }
    result = diagnose_provider_activation(provider, require_reachable=True)
    assert result["activated_count"] == 1
    assert result["ready_count"] == 0


def test_malformed_list_entries_are_safe():
    providers = ["not_a_dict", 42, None, {"provider": "ok", "status": "inactive"}]
    result = diagnose_provider_activation(providers)
    assert result["total_providers"] == 4
    assert result["diagnostics"][0]["issues"] == ["malformed_provider_entry"]
    assert result["diagnostics"][1]["issues"] == ["malformed_provider_entry"]
    assert result["diagnostics"][2]["issues"] == ["malformed_provider_entry"]
    assert result["diagnostics"][3]["provider"] == "ok"


def test_missing_required_fields_reported():
    provider = {"provider": "openai"}
    result = diagnose_provider_activation(provider)
    diag = result["diagnostics"][0]
    assert "status" in diag["missing_fields"]
    assert "missing_or_invalid_status" in diag["issues"]


def test_unrecognized_status_warning():
    provider = {"provider": "openai", "status": "weird"}
    result = diagnose_provider_activation(provider)
    diag = result["diagnostics"][0]
    assert any("unrecognized_status" in w for w in diag["warnings"])


def test_active_without_configured_warning():
    provider = {
        "provider": "openai",
        "status": "active",
        "configured": False,
        "has_credentials": True,
        "reachable": True,
    }
    result = diagnose_provider_activation(provider)
    diag = result["diagnostics"][0]
    assert "active_without_configured_flag" in diag["warnings"]
    assert diag["activated"] is False


def test_invalid_provider_name():
    provider = {"provider": "", "status": "active", "configured": True, "has_credentials": True}
    result = diagnose_provider_activation(provider)
    diag = result["diagnostics"][0]
    assert "missing_or_invalid_provider_name" in diag["issues"]
    assert diag["provider"] is None


def test_unknown_input_shape_returns_empty():
    result = diagnose_provider_activation(12345)
    assert result["total_providers"] == 0
    assert result["diagnostics"] == []


def test_multiple_providers_summary():
    providers = [
        {"provider": "openai", "status": "active", "configured": True, "has_credentials": True, "reachable": True},
        {"provider": "local_llama", "status": "inactive", "configured": True, "has_credentials": False, "reachable": False},
        {"provider": "anthropic", "status": "configured", "configured": True, "has_credentials": True, "reachable": False},
    ]
    result = diagnose_provider_activation(providers)
    assert result["total_providers"] == 3
    assert result["activated_count"] == 1
    assert result["ready_count"] == 1
    assert result["issue_count"] == 0
    assert result["healthy"] is True


def test_providers_with_issues_populated():
    providers = [
        {"provider": "openai", "status": "active", "configured": True, "has_credentials": False},
        {"provider": "local", "status": "inactive", "configured": True, "has_credentials": True},
    ]
    result = diagnose_provider_activation(providers)
    assert len(result["providers_with_issues"]) == 1
    assert result["providers_with_issues"][0]["provider"] == "openai"


def test_function_never_raises_on_garbage():
    # Should not raise for any input.
    for bad in [None, [], {}, "string", 42, [None, [1, 2], {"a": 1}]]:
        result = diagnose_provider_activation(bad)
        assert isinstance(result, dict)
        assert "diagnostics" in result


def test_core_module_importable():
    assert hasattr(core, "diagnose_provider_activation")
    assert hasattr(core, "REQUIRED_PROVIDER_FIELDS")
    assert hasattr(core, "VALID_STATUSES")
