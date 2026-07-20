from __future__ import annotations
import json
import os
import urllib.error
import urllib.request
from .code_contract import CodeContract
from .model_router import ModelRouter
from .execution_budget import ExecutionBudget

class OpenRouterCoderAdapter:
    """253: live OpenRouter coder using the existing OPENROUTER_API_KEY."""

    ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self):
        self.contract = CodeContract()
        self.router = ModelRouter()
        self.budget = ExecutionBudget()

    @property
    def configured(self):
        return bool(os.environ.get("OPENROUTER_API_KEY", "").strip())

    def _system_prompt(self):
        return (
            'You are the CompanyOS autonomous coding agent. '
            'Return ONLY one JSON object with top-level shape '
            '{"files":{"relative/path.py":"complete file content"},"metadata":{}}. '
            'No markdown fences and no prose outside JSON. '
            'Use relative paths only. Include or update tests. '
            'Preserve unrelated behavior and keep changes reversible.'
        )

    def _request(self, model, prompt_payload):
        key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not key:
            return {"success": False, "reason": "OPENROUTER_API_KEY_not_loaded", "files": {}}

        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": self._system_prompt()},
                {"role": "user", "content": json.dumps(prompt_payload, default=str)},
            ],
            "temperature": 0.1,
        }

        req = urllib.request.Request(
            self.ENDPOINT,
            data=json.dumps(body).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.environ.get("COMPANYOS_APP_URL", "https://localhost/companyos"),
                "X-Title": "CompanyOS Autonomous Builder",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=self.budget.limits()["timeout_seconds"]) as response:
                raw = response.read().decode("utf-8", errors="replace")
                status = response.status
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")[-8000:]
            return {"success": False, "reason": f"http_error:{exc.code}", "details": details, "files": {}, "model": model}
        except Exception as exc:
            return {"success": False, "reason": f"connection_error:{type(exc).__name__}:{exc}", "files": {}, "model": model}

        try:
            data = json.loads(raw)
            content = data["choices"][0]["message"]["content"]
        except Exception as exc:
            return {"success": False, "reason": f"unexpected_response:{type(exc).__name__}", "raw": raw[-8000:], "files": {}, "model": model}

        normalized = self.contract.normalize(content)
        return {**normalized, "http_status": status, "model": data.get("model", model), "usage": data.get("usage", {})}

    def generate(self, prompt_payload):
        if not self.configured:
            return {"success": False, "reason": "OPENROUTER_API_KEY_not_loaded", "files": {}}

        errors = []
        for model in self.router.routing_plan()["all_models"]:
            result = self._request(model, prompt_payload)
            if result.get("success"):
                return result
            errors.append({"model": model, "reason": result.get("reason")})

        return {"success": False, "reason": "all_models_failed", "attempts": errors, "files": {}}
