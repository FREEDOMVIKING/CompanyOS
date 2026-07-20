"""Internal provider activation diagnostics for CompanyOS.

This package provides a pure-Python, side-effect free capability that
inspects provider activation/health data and returns structured diagnostics.
No network, financial, or external actions are performed.
"""

from .core import diagnose_provider_activation

__all__ = ["diagnose_provider_activation"]
