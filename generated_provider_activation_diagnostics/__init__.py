"""Provider activation diagnostics for CompanyOS.

This package provides internal, read-only diagnostics for provider
activation records. It performs no network access, no financial actions,
and no external actions.
"""

from .core import (
    diagnose_provider_activation,
    ProviderActivationDiagnosticsError,
)

__all__ = [
    "diagnose_provider_activation",
    "ProviderActivationDiagnosticsError",
]
