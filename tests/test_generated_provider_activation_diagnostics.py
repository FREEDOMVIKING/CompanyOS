"""Pytest coverage for generated_provider_activation_diagnostics."""

from generated_provider_activation_diagnostics import diagnose_provider_activation
from generated_provider_activation_diagnostics.core import (
    _coerce_providers,
    _diagnose_single,
    _is_truthy,
)


def test_is_truthy_handles_various_types():
    assert _is_truthy(True) is True
    assert _is_truthy("yes") is True
    assert _is_truthy("on") is True
    assert _is_truthy(1) is True
    assert _is_truthy(False) is False
    assert _is_truthy("") is False
    assert _is_truthy(0) is False
    assert _is_truthy(None) is False
    assert _is_truthy([]) is False


def test_empty_input_returns_safe_report():
    result = diagnose_provider_activation()
    assert result["provider_count"] == 0
    assert result["active_count"] == 0
    assert result["issue_count"] == 0
    assert result["healthy"] is False
    assert result["providers"] == []
    assert "No providers" in result["summary"]


def test_none_input_is_safe():
    result = diagnose_provider_activation(None)
    assert result["provider_count"] == 0
    assert result["healthy"] is False


def test_single_active_provider_dict():
    provider = {
        "provider": "openai",
        "configured": True,
        "usable": True,
        "reachable": True,
    }
    result = diagnose_provider_activation(provider)
    assert result["provider_count"] == 1
    assert result["active_count"] == 1
    assert result["healthy"] is True
    assert result["providers"][0]["activation_state"] == "active"
    assert result["providers"][0]["valid"] is True


def test_list_of_providers():
    providers = [
        {"provider": "openai", "configured": True, "usable": True},
        {"provider": "local_llama", "configured": True, "usable": False},
    ]
    result = diagnose_provider_activation(providers)
    assert result["provider_count"] == 2
    assert result["active_count"] == 1
    assert result["configured_inactive_count"] == 1
    assert result["healthy"] is False


def test_mapping_of_providers():
    providers = {
        "openai": {"configured": True, "usable": True},
        "local_llama": {"configured": True, "usable": True, "reachable": True},
    }
    result = diagnose_provider_activation(providers)
    assert result["provider_count"] == 2
    assert result["active_count"] == 2
    assert result["healthy"] is True
    names = [p["provider"] for p in result["providers"]]
    assert "openai" in names and "local_llama" in names


def test_mapping_with_scalar_values():
    providers = {"openai": True, "local_llama": False}
    result = diagnose_provider_activation(providers)
    assert result["provider_count"] == 2
    # Scalars become 'configured' only; usable defaults to False -> inactive.
    assert result["active_count"] == 0


def test_missing_required_fields_reported():
    provider = {"provider": "openai"}
    result = diagnose_provider_activation(provider)
    assert result["provider_count"] == 1
    assert result["issue_count"] > 0
    assert "missing_fields:configured,usable" in result["providers"][0]["issues"]
    assert result["providers"][0]["valid"] is False


def test_configured_but_not_usable_flagged():
    provider = {"provider": "openai", "configured": True, "usable": False}
    result = diagnose_provider_activation(provider)
    assert result["providers"][0]["activation_state"] == "configured_inactive"
    assert "configured_but_not_usable" in result["providers"][0]["issues"]


def test_usable_without_configuration_flagged():
    provider = {"provider": "openai", "configured": False, "usable": True}
    result = diagnose_provider_activation(provider)
    assert result["providers"][0]["activation_state"] == "usable_unconfigured"
    assert "usable_without_configuration" in result["providers"][0]["issues"]


def test_usable_but_not_reachable_flagged():
    provider = {
        "provider": "openai",
        "configured": True,
        "usable": True,
        "reachable": False,
    }
    result = diagnose_provider_activation(provider)
    assert result["providers"][0]["activation_state"] == "active"
    assert "usable_but_not_reachable" in result["providers"][0]["issues"]
    assert result["providers"][0]["valid"] is False


def test_missing_provider_name_handled():
    provider = {"configured": True, "usable": True}
    result = diagnose_provider_activation(provider)
    assert result["provider_count"] == 1
    assert "missing_provider_name" in result["providers"][0]["issues"]
    assert result["providers"][0]["provider"].startswith("unnamed_")


def test_malformed_list_entries_handled():
    providers = [
        "openai",  # string entry
        42,  # numeric entry
        None,  # null entry
        {"provider": "local_llama", "configured": True, "usable": True},
    ]
    result = diagnose_provider_activation(providers)
    assert result["provider_count"] == 4
    assert result["active_count"] == 1
    # The first three entries lack configured/usable fields.
    assert result["issue_count"] > 0


def test_coerce_providers_with_unknown_type():
    assert _coerce_providers(object()) == []


def test_coerce_providers_with_scalar():
    result = _coerce_providers("openai")
    assert result == [{"provider": "openai"}]


def test_diagnose_single_directly():
    entry = {"provider": "openai", "configured": True, "usable": True}
    diag = _diagnose_single(entry, 0)
    assert diag["provider"] == "openai"
    assert diag["activation_state"] == "active"
    assert diag["valid"] is True
    assert diag["issues"] == []


def test_all_inactive_not_healthy():
    providers = [
        {"provider": "a", "configured": False, "usable": False},
        {"provider": "b", "configured": False, "usable": False},
    ]
    result = diagnose_provider_activation(providers)
    assert result["active_count"] == 0
    assert result["inactive_count"] == 2
    assert result["healthy"] is False


def test_string_truthy_values():
    provider = {
        "provider": "openai",
        "configured": "true",
        "usable": "yes",
        "reachable": "enabled",
    }
    result = diagnose_provider_activation(provider)
    assert result["providers"][0]["configured"] is True
    assert result["providers"][0]["usable"] is True
    assert result["providers"][0]["reachable"] is True
    assert result["active_count"] == 1


def test_summary_contains_counts():
    providers = [
        {"provider": "openai", "configured": True, "usable": True},
        {"provider": "local_llama", "configured": True, "usable": False},
    ]
    result = diagnose_provider_activation(providers)
    assert "1 active" in result["summary"]
    assert "1 configured_inactive" in result["summary"]


def test_no_external_side_effects():
    """Ensure the function is pure and does not touch the filesystem."""
    import os
    before = os.listdir(".")
    diagnose_provider_activation(
        [{"provider": "openai", "configured": True, "usable": True}]
    )
    after = os.listdir(".")
    assert before == after
