from __future__ import annotations
from typing import Any, Dict

from companyos_phase253_260 import OpenRouterCoderAdapter
from .response_extractor import ResponseExtractor
from .json_recovery import JsonRecovery
from .contract_repair import ContractRepair
from .output_diagnostics import OutputDiagnostics
from .generation_retry import GenerationRetry

class ResilientOpenRouterAdapter:
    """274: wrap OpenRouter generation with recovery + format retry.

    The underlying OpenRouter adapter still handles authentication/model routing.
    This layer improves malformed-output recovery before a build is declared failed.
    """

    def __init__(self, base=None, max_format_retries=2):
        self.base = base or OpenRouterCoderAdapter()
        self.extractor = ResponseExtractor()
        self.recovery = JsonRecovery()
        self.contract = ContractRepair()
        self.diagnostics = OutputDiagnostics()
        self.retry = GenerationRetry()
        self.max_format_retries = max(0, int(max_format_retries))

    @property
    def configured(self):
        return self.base.configured

    def _recover_from_any(self, payload: Any) -> Dict[str, Any]:
        texts = self.extractor.extract(payload)
        if not texts and isinstance(payload, str):
            texts = [payload]

        last_recovery = {"success": False}
        last_contract = {"success": False, "reason": "no_candidate"}

        for text in texts:
            recovered = self.recovery.parse(text)
            last_recovery = recovered
            if not recovered.get("success"):
                continue
            normalized = self.contract.normalize(recovered["data"])
            last_contract = normalized
            if normalized.get("success"):
                return {
                    **normalized,
                    "recovered": True,
                    "recovery_method": recovered.get("method"),
                }

        return {
            "success": False,
            "reason": last_contract.get("reason") or last_recovery.get("reason") or "recovery_failed",
            "diagnostics": self.diagnostics.summarize(
                payload,
                len(texts),
                last_recovery,
                last_contract,
            ),
            "files": {},
        }

    def generate(self, prompt_payload: Dict[str, Any]) -> Dict[str, Any]:
        # Normal first attempt.
        result = self.base.generate(prompt_payload)
        if result.get("success"):
            return result

        # Some base-adapter failures already contain raw provider text.
        recovered = self._recover_from_any(
            result.get("raw")
            or result.get("details")
            or result
        )
        if recovered.get("success"):
            return {
                **recovered,
                "model": result.get("model"),
                "usage": result.get("usage", {}),
            }

        diagnostics = recovered.get("diagnostics", {})
        prompt = prompt_payload

        # Retry specifically for formatting/contract failures.
        for attempt in range(1, self.max_format_retries + 1):
            prompt = self.retry.retry_prompt(prompt_payload, diagnostics, attempt)
            retried = self.base.generate(prompt)
            if retried.get("success"):
                return {
                    **retried,
                    "format_retry_used": True,
                    "format_retry_attempt": attempt,
                }

            recovered_retry = self._recover_from_any(
                retried.get("raw")
                or retried.get("details")
                or retried
            )
            if recovered_retry.get("success"):
                return {
                    **recovered_retry,
                    "model": retried.get("model"),
                    "usage": retried.get("usage", {}),
                    "format_retry_used": True,
                    "format_retry_attempt": attempt,
                }

            diagnostics = recovered_retry.get("diagnostics", diagnostics)

        return {
            "success": False,
            "reason": "resilient_generation_failed",
            "files": {},
            "diagnostics": diagnostics,
        }
