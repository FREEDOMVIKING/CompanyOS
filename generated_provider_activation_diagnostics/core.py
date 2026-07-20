#!/usr/bin/env python3

from typing import Any, Dict, List, Optional


def get_provider_activation_diagnostics(
    provider_name: str,
    configuration: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Analyzes the activation status and potential issues of a given provider.

    This function simulates checking the activation status of a provider based
    on its name and provided configuration. It does not perform any external
    or financial actions.

    Args:
        provider_name: The name of the provider to check.
        configuration: An optional dictionary of configuration parameters for the provider.

    Returns:
        A dictionary containing diagnostic information about the provider's activation.
        The structure includes:
        - 'provider_name': The name of the provider.
        - 'is_active': Boolean indicating if the provider is considered active.
        - 'status': A string describing the current status (e.g., 'active', 'inactive', 'misconfigured').
        - 'diagnostics': A list of strings detailing any identified issues or checks.
        - 'configuration_used': The configuration that was used for the check.
    """
    if not isinstance(provider_name, str) or not provider_name:
        return {
            "provider_name": provider_name,
            "is_active": False,
            "status": "error: invalid_provider_name",
            "diagnostics": ["Provider name must be a non-empty string."],
            "configuration_used": configuration,
        }

    if configuration is None:
        configuration = {}
    elif not isinstance(configuration, dict):
        return {
            "provider_name": provider_name,
            "is_active": False,
            "status": "error: invalid_configuration_type",
            "diagnostics": ["Configuration must be a dictionary or None."],
            "configuration_used": configuration,
        }

    is_active = False
    status = "unknown"
    diagnostics: List[str] = []

    # Simulate activation checks based on provider name and configuration
    if provider_name == "openai":
        if configuration.get("api_key") and configuration.get("api_key") != "dummy_key_for_testing":
            is_active = True
            status = "active"
            diagnostics.append("OpenAI API key is present.")
        else:
            status = "misconfigured"
            diagnostics.append("OpenAI API key is missing or invalid.")
            if not configuration.get("api_key"):
                diagnostics.append("Missing 'api_key' in configuration.")

    elif provider_name == "local_llama":
        if configuration.get("model_path") and configuration.get("port"):
            is_active = True
            status = "active"
            diagnostics.append("Local Llama model path and port are configured.")
        else:
            status = "misconfigured"
            diagnostics.append("Local Llama model path or port is missing.")
            if not configuration.get("model_path"):
                diagnostics.append("Missing 'model_path' in configuration.")
            if not configuration.get("port"):
                diagnostics.append("Missing 'port' in configuration.")

    elif provider_name == "dummy_provider":
        if configuration.get("enabled", False):
            is_active = True
            status = "active"
            diagnostics.append("Dummy provider is enabled.")
        else:
            status = "inactive"
            diagnostics.append("Dummy provider is not enabled.")

    else:
        status = "unsupported"
        diagnostics.append(f"Provider '{provider_name}' is not recognized or supported.")

    return {
        "provider_name": provider_name,
        "is_active": is_active,
        "status": status,
        "diagnostics": diagnostics,
        "configuration_used": configuration,
    }
