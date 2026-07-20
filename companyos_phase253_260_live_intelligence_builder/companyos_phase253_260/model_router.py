from __future__ import annotations
import os

class ModelRouter:
    """255: choose live coding models without permanently hardcoding one."""

    def primary_model(self):
        return os.environ.get("COMPANYOS_OPENROUTER_MODEL", "openrouter/auto-beta").strip()

    def fallback_models(self):
        raw = os.environ.get("COMPANYOS_OPENROUTER_FALLBACK_MODELS", "").strip()
        return [x.strip() for x in raw.split(",") if x.strip()]

    def routing_plan(self):
        primary = self.primary_model()
        fallbacks = [m for m in self.fallback_models() if m != primary]
        return {"primary": primary, "fallbacks": fallbacks, "all_models": [primary, *fallbacks]}
