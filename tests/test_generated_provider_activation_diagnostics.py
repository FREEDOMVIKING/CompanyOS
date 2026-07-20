"""Tests for generated_provider_activation_diagnostics."""

from generated_provider_activation_diagnostics import diagnose_provider_activation
from generated_provider_activation_diagnostics.core import (
    _coerce_bool,
    _coerce_dict,
    _coerce_list,
    _coerce_str,
    _diagnose_single_provider,
)


def test_empty_input_returns_safe_report():
    result = diagnose_provider_activation(None)
    assert result["success"] is True
    assert result["provider_count"] == 0
    assert result["healthy_count"] == 0
    assert result["unhealthy_count"] == 0
    assert result["overall_healthy"] is False
    assert len(result["recommendations"]) > 0
    assert result["external_actions_performed"] is False
    assert result["network_access_performed"] is False
    assert result["financial_actions_performed"] is False


def test_empty_dict_input():
    result = diagnose_provider_activation({})
    assert result["provider_count"] == 0
    assert result["overall_healthy"] is False


def test_empty_list_input():
    result = diagnose_provider_activation([])
    assert result["provider_count"] == 0


def test_malformed_string_input():
    result = diagnose_provider_activation("not a dict or list")
    assert result["success"] is True
    assert result["provider_count"] == 0


def test_malformed_int_input():
    result = diagnose_provider_activation(42)
    assert result["success"] is True
    assert result["provider_count"] == 0


def test_single_healthy_provider():
    data = {
        "providers": [
            {
                "provider": "openai",
                "status": "active",
                "configured": True,
                "usable": True,
                "reachable": True,
            }
        ]
    }
    result = diagnose_provider_activation(data)
    assert result["provider_count"] == 1
    assert result["healthy_count"] == 1
    assert result["unhealthy_count"] == 0
    assert result["overall_healthy"] is True
    assert result["providers"][0]["healthy"] is True
    assert result["providers"][0]["issues"] == []


def test_unconfigured_provider():
    data = {
        "providers": [
            {
                "provider": "openai",
                "status": "unconfigured",
                "configured": False,
                "usable": False,
                "reachable": False,
            }
        ]
    }
    result = diagnose_provider_activation(data)
    assert result["overall_healthy"] is False
    assert result["unhealthy_count"] == 1
    assert "provider_not_configured" in result["providers"][0]["issues"]


def test_configured_but_not_usable():
    data = {
        "providers": [
            {
                "provider": "openai",
                "status": "inactive",
                "configured": True,
                "usable": False,
                "reachable": True,
            }
        ]
    }
    result = diagnose_provider_activation(data)
    assert result["overall_healthy"] is False
    issues = result["providers"][0]["issues"]
    assert "configured_but_not_usable" in issues
    assert "configured_but_inactive" in issues


def test_degraded_provider():
    data = {
        "providers": [
            {
                "provider": "local_llama",
                "status": "degraded",
                "configured": True,
                "usable": True,
                "reachable": True,
            }
        ]
    }
    result = diagnose_provider_activation(data)
    assert result["overall_healthy"] is False
    assert "provider_degraded" in result["providers"][0]["issues"]


def test_primary_fallback_style_input():
    data = {
        "primary": {
            "provider": "openai",
            "status": "active",
            "configured": True,
            "usable": True,
            "reachable": True,
        },
        "fallback": {
            "provider": "local_llama",
            "status": "active",
            "configured": True,
            "usable": True,
            "reachable": True,
        },
    }
    result = diagnose_provider_activation(data)
    assert result["provider_count"] == 2
    assert result["overall_healthy"] is True


def test_list_of_providers_input():
    data = [
        {
            "provider": "openai",
            "status": "active",
            "configured": True,
            "usable": True,
            "reachable": True,
        },
        {
            "provider": "local_llama",
            "status": "inactive",
            "configured": True,
            "usable": False,
            "reachable": False,
        },
    ]
    result = diagnose_provider_activation(data)
    assert result["provider_count"] == 2
    assert result["healthy_count"] == 1
    assert result["unhealthy_count"] == 1
    assert result["overall_healthy"] is False


def test_unknown_provider_name():
    data = {
        "providers": [
            {
                "provider": "mystery_provider",
                "status": "active",
                "configured": True,
                "usable": True,
                "reachable": True,
            }
        ]
    }
    result = diagnose_provider_activation(data)
    assert "unknown_provider_name" in result["providers"][0]["issues"]


def test_invalid_status():
    data = {
        "providers": [
            {
                "provider": "openai",
                "status": "bogus_status",
                "configured": True,
                "usable": True,
                "reachable": True,
            }
        ]
    }
    result = diagnose_provider_activation(data)
    assert "invalid_status" in result["providers"][0]["issues"]


def test_fallback_provider_not_present():
    data = {
        "providers": [
            {
                "provider": "openai",
                "status": "active",
                "configured": True,
                "usable": True,
                "reachable": True,
            }
        ]
    }
    result = diagnose_provider_activation(data, fallback_provider="local_llama")
    assert result["fallback_provider"] == "local_llama"
    assert any("local_llama" in r for r in result["recommendations"])


def test_fallback_provider_present():
    data = {
        "providers": [
            {
                "provider": "openai",
                "status": "active",
                "configured": True,
                "usable": True,
                "reachable": True,
            },
            {
                "provider": "local_llama",
                "status": "active",
                "configured": True,
                "usable": True,
                "reachable": True,
            },
        ]
    }
    result = diagnose_provider_activation(data, fallback_provider="local_llama")
    assert result["overall_healthy"] is True
    assert not any("not present" in r for r in result["recommendations"])


def test_malformed_provider_entry():
    data = {"providers": ["not a dict", None, 42]}
    result = diagnose_provider_activation(data)
    assert result["provider_count"] == 3
    assert result["healthy_count"] == 0
    for diag in result["providers"]:
        assert diag["healthy"] is False


def test_malformed_providers_key():
    data = {"providers": "not a list"}
    result = diagnose_provider_activation(data)
    assert result["provider_count"] == 0


def test_coerce_dict():
    assert _coerce_dict({"a": 1}) == {"a": 1}
    assert _coerce_dict(None) == {}
    assert _coerce_dict("x") == {}
    assert _coerce_dict(42) == {}


def test_coerce_list():
    assert _coerce_list([1, 2]) == [1, 2]
    assert _coerce_list(None) == []
    assert _coerce_list("x") == []


def test_coerce_str():
    assert _coerce_str("  hello  ") == "hello"
    assert _coerce_str(42) == ""
    assert _coerce_str(None) == ""


def test_coerce_bool():
    assert _coerce_bool(True) is True
    assert _coerce_bool(False) is False
    assert _coerce_bool(1) is False
    assert _coerce_bool(None) is False


def test_diagnose_single_provider_empty():
    result = _diagnose_single_provider({})
    assert result["provider"] == "unknown"
    assert result["healthy"] is False
    assert "unknown_provider_name" in result["issues"]


def test_diagnose_single_provider_not_dict():
    result = _diagnose_single_provider("bad")
    assert result["provider"] == "unknown"
    assert result["healthy"] is False


def test_no_external_actions_flags():
    result = diagnose_provider_activation({"providers": []})
    assert result["external_actions_performed"] is False
    assert result["network_access_performed"] is False
    assert result["financial_actions_performed"] is False


def test_multiple_mixed_providers():
    data = {
        "providers": [
            {
                "provider": "openai",
                "status": "active",
                "configured": True,
                "usable": True,
                "reachable": True,
            },
            {
                "provider": "local_llama",
                "status": "degraded",
                "configured": True,
                "usable": True,
                "reachable": False,
            },
            {
                "provider": "anthropic",
                "status": "unconfigured",
                "configured": False,
                "usable": False,
                "reachable": False,
            },
        ]
    }
    result = diagnose_provider_activation(data)
    assert result["provider_count"] == 3
    assert result["healthy_count"] == 1
    assert result["unhealthy_count"] == 2
    assert result["overall_healthy"] is False
    assert len(result["recommendations"]) > 0


def test_public_function_exported():
    from generated_provider_activation_diagnostics import diagnose_provider_activation as fn
    assert callable(fn)
