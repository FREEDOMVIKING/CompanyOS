"""Pytest coverage for generated_provider_activation_diagnostics."""

from __future__ import annotations

import generated_provider_activation_diagnostics as pkg
from generated_provider_activation_diagnostics import (
    core,
    diagnose_provider_activation,
)


class TestPublicAPI:
    def test_package_exposes_function(self):
        assert callable(pkg.diagnose_provider_activation)

    def test_core_module_exists(self):
        assert hasattr(core, "diagnose_provider_activation")


class TestEmptyAndMalformed:
    def test_none_input(self):
        result = diagnose_provider_activation(None)
        assert result["success"] is True
        assert result["provider_count"] == 0
        assert "providers_config_missing" in result["issues"]
        assert result["recommendations"]

    def test_non_dict_input(self):
        result = diagnose_provider_activation("not a dict")
        assert result["success"] is True
        assert "providers_config_not_dict" in result["issues"]

    def test_empty_dict_input(self):
        result = diagnose_provider_activation({})
        assert result["success"] is True
        assert result["provider_count"] == 0
        assert "providers_config_empty" in result["issues"]

    def test_list_input_treated_as_non_dict(self):
        result = diagnose_provider_activation([{"activated": True}])
        assert "providers_config_not_dict" in result["issues"]

    def test_malformed_provider_entry(self):
        result = diagnose_provider_activation({"bad": "just-a-string"})
        assert result["provider_count"] == 1
        diag = result["providers"][0]
        assert diag["valid"] is False
        assert "provider_config_not_dict" in diag["issues"]

    def test_integer_provider_entry(self):
        result = diagnose_provider_activation({"num": 42})
        assert result["providers"][0]["valid"] is False


class TestValidProviders:
    def test_activated_provider_with_api_key(self):
        providers = {
            "openai": {
                "activated": True,
                "api_key": "sk-test",
                "priority": 1,
            }
        }
        result = diagnose_provider_activation(providers)
        assert result["provider_count"] == 1
        assert result["activated_count"] == 1
        assert result["usable_count"] == 1
        assert result["providers"][0]["usable"] is True
        assert result["providers"][0]["issues"] == []

    def test_not_activated_provider(self):
        providers = {
            "openai": {
                "activated": False,
                "api_key": "sk-test",
                "priority": 1,
            }
        }
        result = diagnose_provider_activation(providers)
        assert result["activated_count"] == 0
        assert result["usable_count"] == 0
        assert "not_activated" in result["issues"]

    def test_missing_api_key(self):
        providers = {
            "openai": {
                "activated": True,
                "priority": 1,
            }
        }
        result = diagnose_provider_activation(providers)
        assert "missing_api_key" in result["issues"]
        assert result["usable_count"] == 0

    def test_local_provider_without_api_key(self):
        providers = {
            "local_llama": {
                "activated": True,
                "local": True,
                "priority": 2,
            }
        }
        result = diagnose_provider_activation(providers)
        assert result["usable_count"] == 1
        assert "missing_api_key" not in result["issues"]

    def test_invalid_priority(self):
        providers = {
            "openai": {
                "activated": True,
                "api_key": "sk-test",
                "priority": -5,
            }
        }
        result = diagnose_provider_activation(providers)
        assert "invalid_priority" in result["issues"]

    def test_fallback_without_credentials(self):
        providers = {
            "local_llama": {
                "activated": True,
                "fallback": True,
                "priority": 2,
            }
        }
        result = diagnose_provider_activation(providers)
        assert "fallback_without_credentials" in result["issues"]

    def test_string_activated_values(self):
        providers = {
            "openai": {
                "activated": "true",
                "api_key": "sk-test",
                "priority": 1,
            }
        }
        result = diagnose_provider_activation(providers)
        assert result["activated_count"] == 1

    def test_multiple_providers(self):
        providers = {
            "openai": {
                "activated": True,
                "api_key": "sk-test",
                "priority": 1,
            },
            "local_llama": {
                "activated": True,
                "local": True,
                "fallback": True,
                "priority": 2,
            },
            "disabled": {
                "activated": False,
                "api_key": "",
                "priority": 3,
            },
        }
        result = diagnose_provider_activation(providers)
        assert result["provider_count"] == 3
        assert result["activated_count"] == 2
        assert result["usable_count"] == 2


class TestRoutingPolicy:
    def test_compatible_policy(self):
        providers = {
            "openai": {
                "activated": True,
                "api_key": "sk-test",
                "priority": 1,
            },
            "local_llama": {
                "activated": True,
                "local": True,
                "priority": 2,
            },
        }
        policy = {
            "primary_provider": "openai",
            "fallback_provider": "local_llama",
        }
        result = diagnose_provider_activation(providers, routing_policy=policy)
        assert result["routing_policy_compatible"] is True

    def test_unknown_primary(self):
        providers = {
            "openai": {
                "activated": True,
                "api_key": "sk-test",
                "priority": 1,
            }
        }
        policy = {"primary_provider": "anthropic"}
        result = diagnose_provider_activation(providers, routing_policy=policy)
        assert result["routing_policy_compatible"] is False
        assert "routing_policy_primary_provider_unknown" in result["issues"]

    def test_primary_not_usable(self):
        providers = {
            "openai": {
                "activated": False,
                "api_key": "sk-test",
                "priority": 1,
            }
        }
        policy = {"primary_provider": "openai"}
        result = diagnose_provider_activation(providers, routing_policy=policy)
        assert result["routing_policy_compatible"] is False
        assert "routing_policy_primary_provider_not_usable" in result["issues"]

    def test_malformed_policy(self):
        providers = {
            "openai": {
                "activated": True,
                "api_key": "sk-test",
                "priority": 1,
            }
        }
        result = diagnose_provider_activation(
            providers, routing_policy="not-a-dict"
        )
        assert result["routing_policy_compatible"] is False
        assert "routing_policy_not_dict" in result["issues"]

    def test_no_policy_means_none(self):
        providers = {
            "openai": {
                "activated": True,
                "api_key": "sk-test",
                "priority": 1,
            }
        }
        result = diagnose_provider_activation(providers)
        assert result["routing_policy_compatible"] is None


class TestStructure:
    def test_result_keys(self):
        result = diagnose_provider_activation({})
        expected_keys = {
            "success",
            "status",
            "provider_count",
            "activated_count",
            "usable_count",
            "providers",
            "issues",
            "recommendations",
            "routing_policy_compatible",
        }
        assert expected_keys.issubset(result.keys())

    def test_provider_diagnosis_keys(self):
        providers = {
            "openai": {
                "activated": True,
                "api_key": "sk-test",
                "priority": 1,
            }
        }
        result = diagnose_provider_activation(providers)
        diag = result["providers"][0]
        expected = {
            "provider_id",
            "valid",
            "activated",
            "issues",
            "recommendations",
            "usable",
        }
        assert expected.issubset(diag.keys())

    def test_never_raises(self):
        # Exercise a variety of weird inputs to ensure no exception propagates.
        weird_inputs = [
            None,
            {},
            [],
            "",
            123,
            {"p": None},
            {"p": []},
            {"p": {"activated": "yes", "api_key": 0}},
            {"p": {"priority": "high"}},
        ]
        for inp in weird_inputs:
            result = diagnose_provider_activation(inp)
            assert result["success"] is True
            assert isinstance(result["providers"], list)
            assert isinstance(result["issues"], list)
            assert isinstance(result["recommendations"], list)

    def test_dedup_issues(self):
        providers = {
            "a": {"activated": False, "api_key": "", "priority": -1},
            "b": {"activated": False, "api_key": "", "priority": -1},
        }
        result = diagnose_provider_activation(providers)
        # Each issue should appear only once in the aggregate list.
        assert result["issues"].count("not_activated") == 1
        assert result["issues"].count("missing_api_key") == 1
        assert result["issues"].count("invalid_priority") == 1
