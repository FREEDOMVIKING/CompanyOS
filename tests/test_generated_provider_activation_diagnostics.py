from __future__ import annotations

import pytest

from generated_provider_activation_diagnostics import (
    diagnose_provider_activation,
    ProviderActivationDiagnosticsError,
)


def test_empty_input_returns_empty_state_report():
    result = diagnose_provider_activation()
    assert result["success"] is True
    assert result["status"] == "provider_activation_diagnostics_complete"
    assert result["summary"]["total_providers"] == 0
    assert result["summary"]["overall_status"] == "empty"
    assert result["summary"]["activation_ready"] == 0
    assert result["providers"] == []
    assert result["external_actions_performed"] is False
    assert result["network_access_performed"] is False
    assert result["financial_actions_performed"] is False


def test_none_input_returns_empty_state_report():
    result = diagnose_provider_activation(None)
    assert result["summary"]["total_providers"] == 0


def test_empty_list_returns_empty_state_report():
    result = diagnose_provider_activation([])
    assert result["summary"]["total_providers"] == 0


def test_fully_active_primary_and_fallback_is_healthy():
    providers = [
        {
            "provider": "openai",
            "role": "primary",
            "activation_state": "active",
            "configured": True,
            "usable": True,
            "reachable": True,
            "healthy": True,
        },
        {
            "provider": "local_llama",
            "role": "fallback",
            "activation_state": "active",
            "configured": True,
            "usable": True,
            "reachable": True,
            "healthy": True,
        },
    ]
    result = diagnose_provider_activation(providers)
    assert result["summary"]["total_providers"] == 2
    assert result["summary"]["activation_ready"] == 2
    assert result["summary"]["primary_ready"] is True
    assert result["summary"]["fallback_ready"] is True
    assert result["summary"]["overall_status"] == "healthy"
    assert result["summary"]["severity_counts"]["ok"] == 2
    assert all(p["activation_ready"] for p in result["providers"])


def test_failed_provider_is_high_severity_and_critical():
    providers = [
        {
            "provider": "openai",
            "role": "primary",
            "activation_state": "failed",
            "configured": True,
            "usable": False,
            "reachable": False,
            "healthy": False,
        },
    ]
    result = diagnose_provider_activation(providers)
    diag = result["providers"][0]
    assert diag["activation_state"] == "failed"
    assert diag["severity"] == "high"
    assert diag["activation_ready"] is False
    assert "activation_failed" in diag["issues"]
    assert result["summary"]["overall_status"] == "critical"
    assert result["summary"]["severity_counts"]["high"] == 1


def test_degraded_provider_is_medium_severity():
    providers = [
        {
            "provider": "openai",
            "role": "primary",
            "activation_state": "degraded",
            "configured": True,
            "usable": True,
            "reachable": True,
            "healthy": True,
        },
    ]
    result = diagnose_provider_activation(providers)
    diag = result["providers"][0]
    assert diag["severity"] == "medium"
    assert diag["activation_ready"] is False
    assert result["summary"]["overall_status"] == "degraded"


def test_pending_provider_is_medium_severity_and_attention():
    providers = [
        {
            "provider": "local_llama",
            "role": "fallback",
            "activation_state": "pending",
            "configured": True,
            "usable": True,
            "reachable": True,
            "healthy": True,
        },
    ]
    result = diagnose_provider_activation(providers)
    diag = result["providers"][0]
    assert diag["severity"] == "medium"
    assert diag["activation_ready"] is False
    assert "activation_pending" in diag["issues"]


def test_unknown_state_is_low_severity():
    providers = [
        {
            "provider": "mystery",
            "role": "secondary",
            "activation_state": "weird",
            "configured": True,
            "usable": True,
            "reachable": True,
            "healthy": True,
        },
    ]
    result = diagnose_provider_activation(providers)
    diag = result["providers"][0]
    assert diag["activation_state"] == "unknown"
    assert "activation_state_unknown" in diag["issues"]
    assert diag["severity"] == "low"


def test_missing_optional_fields_default_safely():
    providers = [
        {"provider": "openai"},
    ]
    result = diagnose_provider_activation(providers)
    diag = result["providers"][0]
    assert diag["provider"] == "openai"
    assert diag["role"] == "unknown"
    assert diag["activation_state"] == "unknown"
    assert diag["configured"] is None
    assert diag["usable"] is None
    assert diag["reachable"] is None
    assert diag["healthy"] is None
    assert diag["activation_ready"] is False


def test_missing_provider_name_defaults_to_unnamed():
    providers = [
        {"activation_state": "active", "configured": True, "usable": True,
         "reachable": True, "healthy": True},
    ]
    result = diagnose_provider_activation(providers)
    assert result["providers"][0]["provider"] == "unnamed_provider"


def test_name_mapping_input_sets_provider_name():
    providers = {
        "openai": {
            "role": "primary",
            "activation_state": "active",
            "configured": True,
            "usable": True,
            "reachable": True,
            "healthy": True,
        },
        "local_llama": {
            "role": "fallback",
            "activation_state": "active",
            "configured": True,
            "usable": True,
            "reachable": True,
            "healthy": True,
        },
    }
    result = diagnose_provider_activation(providers)
    names = {p["provider"] for p in result["providers"]}
    assert names == {"openai", "local_llama"}
    assert result["summary"]["activation_ready"] == 2


def test_providers_key_mapping_input():
    providers = {
        "providers": [
            {
                "provider": "openai",
                "role": "primary",
                "activation_state": "active",
                "configured": True,
                "usable": True,
                "reachable": True,
                "healthy": True,
            },
        ]
    }
    result = diagnose_provider_activation(providers)
    assert result["summary"]["total_providers"] == 1
    assert result["providers"][0]["provider"] == "openai"


def test_providers_key_with_none_is_empty():
    result = diagnose_provider_activation({"providers": None})
    assert result["summary"]["total_providers"] == 0


def test_string_input_raises():
    with pytest.raises(ProviderActivationDiagnosticsError):
        diagnose_provider_activation("openai")


def test_non_mapping_list_entry_raises():
    with pytest.raises(ProviderActivationDiagnosticsError):
        diagnose_provider_activation(["openai"])


def test_non_mapping_provider_value_raises():
    with pytest.raises(ProviderActivationDiagnosticsError):
        diagnose_provider_activation({"openai": "active"})


def test_non_list_providers_field_raises():
    with pytest.raises(ProviderActivationDiagnosticsError):
        diagnose_provider_activation({"providers": {"openai": {}}})


def test_non_string_mapping_key_raises():
    with pytest.raises(ProviderActivationDiagnosticsError):
        diagnose_provider_activation({1: {}})


def test_unsupported_input_type_raises():
    with pytest.raises(ProviderActivationDiagnosticsError):
        diagnose_provider_activation(42)


def test_include_records_false_omits_providers():
    providers = [
        {
            "provider": "openai",
            "role": "primary",
            "activation_state": "active",
            "configured": True,
            "usable": True,
            "reachable": True,
            "healthy": True,
        },
    ]
    result = diagnose_provider_activation(providers, include_records=False)
    assert "providers" not in result
    assert result["summary"]["total_providers"] == 1


def test_recommendations_present_for_mixed_states():
    providers = [
        {"provider": "openai", "role": "primary", "activation_state": "failed",
         "configured": True, "usable": False, "reachable": False, "healthy": False},
        {"provider": "local_llama", "role": "fallback", "activation_state": "pending",
         "configured": True, "usable": True, "reachable": True, "healthy": True},
    ]
    result = diagnose_provider_activation(providers)
    recs = result["summary"]["recommendations"]
    assert any("primary" in r for r in recs)
    assert any("fallback" in r for r in recs)
    assert any("failed" in r for r in recs)
    assert any("pending" in r for r in recs)


def test_state_field_alias_works():
    providers = [
        {
            "provider": "openai",
            "role": "primary",
            "state": "active",
            "configured": True,
            "usable": True,
            "reachable": True,
            "healthy": True,
        },
    ]
    result = diagnose_provider_activation(providers)
    assert result["providers"][0]["activation_state"] == "active"
    assert result["providers"][0]["activation_ready"] is True


def test_non_bool_configured_is_ignored_safely():
    providers = [
        {
            "provider": "openai",
            "role": "primary",
            "activation_state": "active",
            "configured": "yes",
            "usable": True,
            "reachable": True,
            "healthy": True,
        },
    ]
    result = diagnose_provider_activation(providers)
    diag = result["providers"][0]
    assert diag["configured"] is None
    assert diag["activation_ready"] is True


def test_inactive_provider_is_low_severity():
    providers = [
        {
            "provider": "legacy",
            "role": "standby",
            "activation_state": "inactive",
            "configured": True,
            "usable": True,
            "reachable": True,
            "healthy": True,
        },
    ]
    result = diagnose_provider_activation(providers)
    diag = result["providers"][0]
    assert diag["severity"] == "low"
    assert "activation_inactive" in diag["issues"]
    assert diag["activation_ready"] is False


def test_all_ready_recommendation_present():
    providers = [
        {
            "provider": "openai",
            "role": "primary",
            "activation_state": "active",
            "configured": True,
            "usable": True,
            "reachable": True,
            "healthy": True,
        },
        {
            "provider": "local_llama",
            "role": "fallback",
            "activation_state": "active",
            "configured": True,
            "usable": True,
            "reachable": True,
            "healthy": True,
        },
    ]
    result = diagnose_provider_activation(providers)
    assert any("activation-ready" in r for r in result["summary"]["recommendations"])


def test_no_external_or_network_flags_are_false():
    result = diagnose_provider_activation(
        [{"provider": "openai", "activation_state": "active",
          "configured": True, "usable": True, "reachable": True, "healthy": True}]
    )
    assert result["external_actions_performed"] is False
    assert result["network_access_performed"] is False
    assert result["financial_actions_performed"] is False


def test_tuple_input_accepted():
    providers = (
        {
            "provider": "openai",
            "role": "primary",
            "activation_state": "active",
            "configured": True,
            "usable": True,
            "reachable": True,
            "healthy": True,
        },
    )
    result = diagnose_provider_activation(providers)
    assert result["summary"]["total_providers"] == 1


def test_role_normalization_unknown_value():
    providers = [
        {"provider": "x", "role": "weird", "activation_state": "active",
         "configured": True, "usable": True, "reachable": True, "healthy": True},
    ]
    result = diagnose_provider_activation(providers)
    assert result["providers"][0]["role"] == "unknown"


def test_summary_counts_are_consistent():
    providers = [
        {"provider": "a", "role": "primary", "activation_state": "active",
         "configured": True, "usable": True, "reachable": True, "healthy": True},
        {"provider": "b", "role": "fallback", "activation_state": "failed",
         "configured": True, "usable": False, "reachable": False, "healthy": False},
        {"provider": "c", "role": "secondary", "activation_state": "degraded",
         "configured": True, "usable": True, "reachable": True, "healthy": True},
        {"provider": "d", "role": "standby", "activation_state": "pending",
         "configured": True, "usable": True, "reachable": True, "healthy": True},
    ]
    result = diagnose_provider_activation(providers)
    s = result["summary"]
    assert s["total_providers"] == 4
    assert s["active"] == 1
    assert s["failed"] == 1
    assert s["degraded"] == 1
    assert s["pending"] == 1
    assert s["activation_ready"] == 1
    assert s["severity_counts"]["high"] == 1
    assert s["severity_counts"]["medium"] == 2
    assert s["overall_status"] == "critical"
