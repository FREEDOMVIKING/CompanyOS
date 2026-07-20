"""Tests for generated_provider_activation_diagnostics."""

from __future__ import annotations

import generated_provider_activation_diagnostics as pkg
from generated_provider_activation_diagnostics import core
from generated_provider_activation_diagnostics import diagnose_provider_activation


def test_package_exposes_public_function():
    assert callable(pkg.diagnose_provider_activation)
    assert pkg.diagnose_provider_activation is core.diagnose_provider_activation


def test_empty_input_is_safe():
    result = diagnose_provider_activation(None)
    assert result["success"] is True
    assert result["provider_count"] == 0
    assert result["providers"] == []
    assert result["summary"]["healthy"] is True
    assert result["recommendations"]


def test_empty_dict_is_safe():
    result = diagnose_provider_activation({})
    assert result["success"] is True
    assert result["provider_count"] == 0
    assert result["issue_count"] == 0


def test_malformed_string_input_is_safe():
    result = diagnose_provider_activation("not-a-dict")
    assert result["success"] is True
    assert result["provider_count"] == 0
    assert result.get("malformed_input") is True


def test_malformed_container_type_is_safe():
    result = diagnose_provider_activation(42)
    assert result["success"] is True
    assert result["provider_count"] == 0
    assert result.get("malformed_input") is True


def test_active_provider_is_usable():
    result = diagnose_provider_activation(
        {
            "openai": {
                "activation_state": "active",
                "configured": True,
                "credentials_present": True,
                "reachable": True,
            }
        }
    )
    assert result["provider_count"] == 1
    assert result["usable_count"] == 1
    provider = result["providers"][0]
    assert provider["provider"] == "openai"
    assert provider["usable"] is True
    assert provider["issues"] == []
    assert result["summary"]["healthy"] is True


def test_not_configured_provider_has_high_severity_issue():
    result = diagnose_provider_activation(
        {
            "openai": {
                "activation_state": "inactive",
                "configured": False,
            }
        }
    )
    provider = result["providers"][0]
    assert provider["configured"] is False
    assert provider["usable"] is False
    codes = [i["code"] for i in provider["issues"]]
    assert "not_configured" in codes
    assert any(i["severity"] == "high" for i in provider["issues"])
    assert result["summary"]["healthy"] is False


def test_missing_credentials_flagged():
    result = diagnose_provider_activation(
        {
            "openai": {
                "activation_state": "configured",
                "configured": True,
                "credentials_present": False,
            }
        }
    )
    provider = result["providers"][0]
    codes = [i["code"] for i in provider["issues"]]
    assert "missing_credentials" in codes
    assert provider["usable"] is False


def test_active_but_unreachable_flagged():
    result = diagnose_provider_activation(
        {
            "local_llama": {
                "activation_state": "active",
                "configured": True,
                "credentials_present": True,
                "reachable": False,
            }
        }
    )
    provider = result["providers"][0]
    codes = [i["code"] for i in provider["issues"]]
    assert "active_but_unreachable" in codes
    assert provider["usable"] is False


def test_failed_activation_with_last_error():
    result = diagnose_provider_activation(
        {
            "openai": {
                "activation_state": "failed",
                "configured": True,
                "credentials_present": True,
                "reachable": False,
                "last_error": "auth token rejected",
            }
        }
    )
    provider = result["providers"][0]
    codes = [i["code"] for i in provider["issues"]]
    assert "activation_failed" in codes
    assert provider["last_error"] == "auth token rejected"
    assert any("auth token rejected" in r for r in provider["recommendations"])


def test_degraded_provider_is_usable_but_flagged():
    result = diagnose_provider_activation(
        {
            "openai": {
                "activation_state": "degraded",
                "configured": True,
                "credentials_present": True,
                "reachable": True,
            }
        }
    )
    provider = result["providers"][0]
    codes = [i["code"] for i in provider["issues"]]
    assert "activation_degraded" in codes
    assert provider["usable"] is True


def test_degraded_and_unreachable_not_usable():
    result = diagnose_provider_activation(
        {
            "openai": {
                "activation_state": "degraded",
                "configured": True,
                "credentials_present": True,
                "reachable": False,
            }
        }
    )
    provider = result["providers"][0]
    assert provider["usable"] is False


def test_unknown_provider_flagged():
    result = diagnose_provider_activation(
        {
            "mystery_provider": {
                "activation_state": "active",
                "configured": True,
                "credentials_present": True,
                "reachable": True,
            }
        }
    )
    provider = result["providers"][0]
    assert provider["known"] is False
    codes = [i["code"] for i in provider["issues"]]
    assert "unknown_provider" in codes


def test_invalid_activation_state_normalized_to_unknown():
    result = diagnose_provider_activation(
        {
            "openai": {
                "activation_state": "bogus_state",
                "configured": True,
                "credentials_present": True,
                "reachable": True,
            }
        }
    )
    provider = result["providers"][0]
    assert provider["activation_state"] == "unknown"


def test_non_dict_entry_handled_safely():
    result = diagnose_provider_activation({"openai": "broken"})
    provider = result["providers"][0]
    assert provider["activation_state"] == "unknown"
    assert provider["configured"] is False
    codes = [i["code"] for i in provider["issues"]]
    assert "malformed_entry" in codes


def test_list_input_with_name_field():
    result = diagnose_provider_activation(
        [
            {
                "provider": "openai",
                "activation_state": "active",
                "configured": True,
                "credentials_present": True,
                "reachable": True,
            }
        ]
    )
    assert result["provider_count"] == 1
    assert result["providers"][0]["provider"] == "openai"


def test_list_input_with_name_alias():
    result = diagnose_provider_activation(
        [
            {
                "name": "local_llama",
                "activation_state": "active",
                "configured": True,
                "credentials_present": True,
                "reachable": True,
            }
        ]
    )
    assert result["provider_count"] == 1
    assert result["providers"][0]["provider"] == "local_llama"


def test_list_input_skips_malformed_entries():
    result = diagnose_provider_activation(
        [
            "not-a-dict",
            {"activation_state": "active"},
            {
                "provider": "openai",
                "activation_state": "active",
                "configured": True,
                "credentials_present": True,
                "reachable": True,
            },
        ]
    )
    assert result["provider_count"] == 1
    assert result["providers"][0]["provider"] == "openai"


def test_duplicate_providers_deduplicated():
    result = diagnose_provider_activation(
        {
            "openai": {
                "activation_state": "active",
                "configured": True,
                "credentials_present": True,
                "reachable": True,
            },
            "openai_dup": {
                "activation_state": "active",
                "configured": True,
                "credentials_present": True,
                "reachable": True,
            },
        }
    )
    names = [p["provider"] for p in result["providers"]]
    assert "openai" in names
    assert "openai_dup" in names
    assert len(names) == 2


def test_inactive_but_ready_flagged_low_severity():
    result = diagnose_provider_activation(
        {
            "openai": {
                "activation_state": "inactive",
                "configured": True,
                "credentials_present": True,
                "reachable": True,
            }
        }
    )
    provider = result["providers"][0]
    codes = [i["code"] for i in provider["issues"]]
    assert "inactive_but_ready" in codes
    assert all(
        i["severity"] == "low"
        for i in provider["issues"]
        if i["code"] == "inactive_but_ready"
    )


def test_global_recommendations_when_no_usable_providers():
    result = diagnose_provider_activation(
        {
            "openai": {
                "activation_state": "inactive",
                "configured": False,
            }
        }
    )
    assert result["usable_count"] == 0
    assert any("usable" in r for r in result["recommendations"])


def test_output_is_json_serializable_structure():
    import json

    result = diagnose_provider_activation(
        {
            "openai": {
                "activation_state": "active",
                "configured": True,
                "credentials_present": True,
                "reachable": True,
                "last_error": None,
            }
        }
    )
    serialized = json.dumps(result)
    assert json.loads(serialized) == result


def test_deterministic_ordering():
    result = diagnose_provider_activation(
        {
            "zeta": {
                "activation_state": "active",
                "configured": True,
                "credentials_present": True,
                "reachable": True,
            },
            "alpha": {
                "activation_state": "active",
                "configured": True,
                "credentials_present": True,
                "reachable": True,
            },
        }
    )
    names = [p["provider"] for p in result["providers"]]
    assert names == ["alpha", "zeta"]
