"""generated_provider_activation_diagnostics

Internal CompanyOS capability for diagnosing AI provider activation state.
This module is purely diagnostic: it inspects provider configuration data and
produces structured diagnostic results. It performs no network access, no
financial actions, and no external actions.
"""

from .core import diagnose_provider_activation

__all__ = ["diagnose_provider_activation"]
