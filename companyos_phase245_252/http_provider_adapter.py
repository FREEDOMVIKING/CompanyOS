from __future__ import annotations
import json, os, urllib.request, urllib.error
from .response_normalizer import ResponseNormalizer

class HttpProviderAdapter:
    """247: provider-neutral HTTP JSON adapter.

    Expected request body:
      {"model": "...", "prompt": <CompanyOS JSON payload>}

    Accepted response:
      {"files": {...}}
    or
      {"text": "{\\"files\\": {...}}"}

    This deliberately avoids hardcoding a vendor-specific API contract.
    """

    def __init__(self, endpoint, model, api_key_env="COMPANYOS_CODER_API_KEY"):
        self.endpoint = str(endpoint)
        self.model = str(model)
        self.api_key_env = str(api_key_env)
        self.normalizer = ResponseNormalizer()

    def invoke(self, prompt_payload, timeout=180):
        key = os.environ.get(self.api_key_env, "")
        body = json.dumps({
            "model": self.model,
            "prompt": prompt_payload,
        }).encode("utf-8")

        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"

        req = urllib.request.Request(
            self.endpoint,
            data=body,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return {"success": False, "reason": f"http_error:{e.code}", "files": {}}
        except Exception as e:
            return {"success": False, "reason": f"connection_error:{type(e).__name__}:{e}", "files": {}}

        try:
            data = json.loads(raw)
        except Exception:
            data = raw

        return self.normalizer.normalize(data)
