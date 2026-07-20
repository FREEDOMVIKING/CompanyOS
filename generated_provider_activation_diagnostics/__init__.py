"""Provider activation diagnostics for CompanyOS.

This package provides internal, read-only diagnostics for AI provider
activation state. It performs no network access, no financial actions, and
no external actions.
"""

from .core import diagnose_provider_activation, ActivationDiagnosticsResult

__all__ = [
    "diagnose_provider_activation",
    "ActivationDiagnosticsResult",
]
