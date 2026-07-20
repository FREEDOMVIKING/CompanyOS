"""Tests for generated_provider_activation_diagnostics."""
from __future__ import annotations

from generated_provider_activation_diagnostics import diagnose_provider_activation
from generated_provider_activation_diagnostics.core import (
    _coerce_providers,
    _diagnose_entry,
)


def test_empty_input_returns_safe_structure():
    result = diagnose_provider_activation(None)
    assert result["success"] is True
    assert result["summary"]["total"] == 0
    assert result["providers"] == []
    assert result["issues"] == []
    assert isinstance(result["recommendations"], list)
    assert result["external_actions_performed"] is False


def test_list_of_well_formed_providers():
    providers = [
        {"provider": "openai", "status": "active", "enabled": True},
        {"provider": "local_llama", "status": "inactive", "enabled": False},
    ]
    result = diagnose_provider_activation(providers)
    assert result["summary"]["total"] == 2
    assert result["summary"]["active"] == 1
    assert result["summary"]["healthy"] == 2
    assert result["summary"]["with_issues"] == 0
    names = [d["provider"] for d in result["providers"]]
    assert names == ["openai", "local_llama"]


def test_dict_keyed_providers():
    providers = {
        "openai": {"status": "active"},
        "local_llama": {"status": "pending"},
    }
    result = diagnose_provider_activation(providers)
    assert result["summary"]["total"] == 2
    providers_by_name = {d["provider"]: d for d in result["providers"]}
    assert providers_by_name["openai"]["activated"] is True
    assert providers_by_name["local_llama"]["status"] == "pending"


def test_malformed_list_entries_are_handled():
    providers = ["openai", 123, None, {"status": "active"}]
    result = diagnose_provider_activation(providers)
    assert result["summary"]["total"] == 4
    assert result["summary"]["with_issues"] >= 3
    assert any(i["issue"] == "malformed_entry" for i in result["issues"])


def test_missing_required_fields_reported():
    providers = [{"provider": "openai"}]
    result = diagnose_provider_activation(providers)
    assert result["summary"]["with_issues"] == 1
    issues = result["providers"][0]["issues"]
    assert any("missing_field:status" in i for i in issues)


def test_invalid_status_reported():
    providers = [{"provider": "openai", "status": "bogus"}]
    result = diagnose_provider_activation(providers)
    diag = result["providers"][0]
    assert diag["status"] == "unknown"
    assert any("invalid_status" in i for i in diag["issues"])


def test_non_dict_config_flagged():
    providers = [{"provider": "openai", "status": "active", "config": "oops"}]
    result = diagnose_provider_activation(providers)
    issues = result["providers"][0]["issues"]
    assert "non_dict_config" in issues


def test_active_but_disabled_warning():
    providers = [{"provider": "openai", "status": "active", "enabled": False}]
    result = diagnose_provider_activation(providers)
    warnings = result["providers"][0]["warnings"]
    assert "active_but_disabled" in warnings
    assert "Reconcile providers marked active but disabled." in result["recommendations"]


def test_error_status_without_detail_warning():
    providers = [{"provider": "openai", "status": "error"}]
    result = diagnose_provider_activation(providers)
    warnings = result["providers"][0]["warnings"]
    assert "error_status_without_detail" in warnings


def test_error_status_with_detail_no_warning():
    providers = [{"provider": "openai", "status": "error", "error_detail": "timeout"}]
    result = diagnose_provider_activation(providers)
    warnings = result["providers"][0]["warnings"]
    assert "error_status_without_detail" not in warnings


def test_non_bool_enabled_warning():
    providers = [{"provider": "openai", "status": "active", "enabled": "yes"}]
    result = diagnose_provider_activation(providers)
    assert "non_bool_enabled" in result["providers"][0]["warnings"]


def test_non_string_provider_flagged():
    providers = [{"provider": 123, "status": "active"}]
    result = diagnose_provider_activation(providers)
    diag = result["providers"][0]
    assert diag["provider"] == "unknown"
    assert "missing_or_non_string_provider" in diag["issues"]


def test_unknown_top_level_type_handled():
    result = diagnose_provider_activation(42)
    assert result["success"] is True
    assert result["summary"]["total"] == 1
    assert result["summary"]["with_issues"] == 1


def test_recommendations_for_no_active_providers():
    providers = [{"provider": "openai", "status": "inactive"}]
    result = diagnose_provider_activation(providers)
    assert "No providers are currently active." in result["recommendations"]


def test_recommendations_all_well_formed():
    providers = [{"provider": "openai", "status": "active", "enabled": True}]
    result = diagnose_provider_activation(providers)
    assert "All provider activation records are well-formed." in result["recommendations"]


def test_coerce_providers_dict_with_non_dict_value():
    out = _coerce_providers({"openai": "not-a-dict"})
    assert len(out) == 1
    assert out[0]["provider"] == "openai"
    assert out[0]["malformed"] is True


def test_diagnose_entry_minimal():
    diag = _diagnose_entry({"provider": "x", "status": "active"})
    assert diag["activated"] is True
    assert diag["healthy"] is True
    assert diag["issues"] == []


def test_no_external_actions_flag():
    result = diagnose_provider_activation([{"provider": "a", "status": "active"}])
    assert result["external_actions_performed"] is False


def test_returns_python_native_types():
    result = diagnose_provider_activation([{"provider": "a", "status": "active"}])
    assert isinstance(result, dict)
    assert isinstance(result["summary"], dict)
    assert isinstance(result["providers"], list)
    assert isinstance(result["issues"], list)
    assert isinstance(result["recommendations"], list)
