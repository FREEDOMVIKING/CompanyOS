"""Provider activation diagnostics for CompanyOS.

This package provides internal, read-only diagnostics for provider
activation state. It performs no network access and no external actions.
"""

from .core import diagnose_provider_activation

__all__ = ["diagnose_provider_activation"]
