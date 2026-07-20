#!/usr/bin/env python3

import pytest

from generated_provider_activation_diagnostics import get_provider_activation_diagnostics


def test_openai_provider_active():
    config = {
        "api_key": "sk-testkey123",
        "model": "gpt-4",
        "temperature": 0.7
    }
    result = get_provider_activation_diagnostics("openai", config)
    assert result["provider_name"] == "openai"
    assert result["is_active"] is True
    assert result["status"] == "active"
    assert "OpenAI API key is present." in result["diagnostics"]
    assert result["configuration_used"] == config

def test_openai_provider_inactive_missing_key():
    config = {
        "model": "gpt-4",
        "temperature": 0.7
    }
    result = get_provider_activation_diagnostics("openai", config)
    assert result["provider_name"] == "openai"
    assert result["is_active"] is False
    assert result["status"] == "misconfigured"
    assert "OpenAI API key is missing or invalid." in result["diagnostics"]
    assert "Missing 'api_key' in configuration." in result["diagnostics"]
    assert result["configuration_used"] == config

def test_openai_provider_inactive_dummy_key():
    config = {
        "api_key": "dummy_key_for_testing",
        "model": "gpt-4",
        "temperature": 0.7
    }
    result = get_provider_activation_diagnostics("openai", config)
    assert result["provider_name"] == "openai"
    assert result["is_active"] is False
    assert result["status"] == "misconfigured"
    assert "OpenAI API key is missing or invalid." in result["diagnostics"]
    assert result["configuration_used"] == config

def test_local_llama_provider_active():
    config = {
        "model_path": "/models/llama-2-7b-chat.gguf",
        "port": 8080,
        "context_length": 4096
    }
    result = get_provider_activation_diagnostics("local_llama", config)
    assert result["provider_name"] == "local_llama"
    assert result["is_active"] is True
    assert result["status"] == "active"
    assert "Local Llama model path and port are configured." in result["diagnostics"]
    assert result["configuration_used"] == config

def test_local_llama_provider_inactive_missing_path():
    config = {
        "port": 8080,
        "context_length": 4096
    }
    result = get_provider_activation_diagnostics("local_llama", config)
    assert result["provider_name"] == "local_llama"
    assert result["is_active"] is False
    assert result["status"] == "misconfigured"
    assert "Local Llama model path or port is missing." in result["diagnostics"]
    assert "Missing 'model_path' in configuration." in result["diagnostics"]
    assert result["configuration_used"] == config

def test_local_llama_provider_inactive_missing_port():
    config = {
        "model_path": "/models/llama-2-7b-chat.gguf",
        "context_length": 4096
    }
    result = get_provider_activation_diagnostics("local_llama", config)
    assert result["provider_name"] == "local_llama"
    assert result["is_active"] is False
    assert result["status"] == "misconfigured"
    assert "Local Llama model path or port is missing." in result["diagnostics"]
    assert "Missing 'port' in configuration." in result["diagnostics"]
    assert result["configuration_used"] == config

def test_dummy_provider_active():
    config = {"enabled": True, "setting": "value"}
    result = get_provider_activation_diagnostics("dummy_provider", config)
    assert result["provider_name"] == "dummy_provider"
    assert result["is_active"] is True
    assert result["status"] == "active"
    assert "Dummy provider is enabled." in result["diagnostics"]
    assert result["configuration_used"] == config

def test_dummy_provider_inactive():
    config = {"enabled": False, "setting": "value"}
    result = get_provider_activation_diagnostics("dummy_provider", config)
    assert result["provider_name"] == "dummy_provider"
    assert result["is_active"] is False
    assert result["status"] == "inactive"
    assert "Dummy provider is not enabled." in result["diagnostics"]
    assert result["configuration_used"] == config

def test_unsupported_provider():
    config = {"setting": "value"}
    result = get_provider_activation_diagnostics("unsupported_provider", config)
    assert result["provider_name"] == "unsupported_provider"
    assert result["is_active"] is False
    assert result["status"] == "unsupported"
    assert "Provider 'unsupported_provider' is not recognized or supported." in result["diagnostics"]
    assert result["configuration_used"] == config

def test_empty_provider_name():
    result = get_provider_activation_diagnostics("", {"setting": "value"})
    assert result["provider_name"] == ""
    assert result["is_active"] is False
    assert result["status"] == "error: invalid_provider_name"
    assert "Provider name must be a non-empty string." in result["diagnostics"]

def test_none_provider_name():
    result = get_provider_activation_diagnostics(None, {"setting": "value"})
    assert result["provider_name"] is None
    assert result["is_active"] is False
    assert result["status"] == "error: invalid_provider_name"
    assert "Provider name must be a non-empty string." in result["diagnostics"]

def test_invalid_configuration_type():
    result = get_provider_activation_diagnostics("openai", ["list", "is", "not", "dict"])
    assert result["provider_name"] == "openai"
    assert result["is_active"] is False
    assert result["status"] == "error: invalid_configuration_type"
    assert "Configuration must be a dictionary or None." in result["diagnostics"]
    assert result["configuration_used"] == ["list", "is", "not", "dict"]

def test_provider_with_no_configuration():
    result = get_provider_activation_diagnostics("dummy_provider")
    assert result["provider_name"] == "dummy_provider"
    assert result["is_active"] is False
    assert result["status"] == "inactive"
    assert "Dummy provider is not enabled." in result["diagnostics"]
    assert result["configuration_used"] == {}

def test_openai_with_empty_config():
    result = get_provider_activation_diagnostics("openai", {})
    assert result["provider_name"] == "openai"
    assert result["is_active"] is False
    assert result["status"] == "misconfigured"
    assert "Missing 'api_key' in configuration." in result["diagnostics"]

def test_local_llama_with_empty_config():
    result = get_provider_activation_diagnostics("local_llama", {})
    assert result["provider_name"] == "local_llama"
    assert result["is_active"] is False
    assert result["status"] == "misconfigured"
    assert "Missing 'model_path' in configuration." in result["diagnostics"]
    assert "Missing 'port' in configuration." in result["diagnostics"]
