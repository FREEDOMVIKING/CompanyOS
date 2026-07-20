"""generated_provider_activation_diagnostics

Internal CompanyOS capability for diagnosing AI provider activation state.

This package is intentionally side-effect free: it performs no network access,
no financial actions, and no external actions. It evaluates provider
configuration and activation signals supplied by the caller and returns
structured diagnostic data.
"""

from .core import diagnose_provider_activation

__all__ = ["diagnose_provider_activation"]
