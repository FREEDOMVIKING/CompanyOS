"""Provider activation diagnostics for CompanyOS.

This package provides internal, read-only diagnostics for AI provider
activation state. It performs no network access and no external actions.
"""

from generated_provider_activation_diagnostics.core import (
    diagnose_provider_activation,
    ProviderActivationDiagnostics,
)

__all__ = [
    "diagnose_provider_activation",
    "ProviderActivationDiagnostics",
]

__version__ = "1.0.0"
