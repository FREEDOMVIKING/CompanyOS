import json
import os
import urllib.request
import urllib.error

class ReasoningClient:
    def __init__(self, url=None, timeout=90):
        self.url = url or os.getenv(
            "COMPANYOS_REASONING_URL",
            "http://127.0.0.1:8765/reason"
        )
        self.timeout = int(timeout)

    def reason(self, messages, metadata=None):
        payload = {
            "messages": messages,
            "metadata": metadata or {}
        }
        req = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", "replace")
                data = json.loads(raw)
        except urllib.error.HTTPError as e:
            return {
                "success": False,
                "error": "reasoning_http_error",
                "status_code": e.code,
                "body": e.read().decode("utf-8", "replace")[:4000]
            }
        except Exception as e:
            return {
                "success": False,
                "error": type(e).__name__,
                "message": str(e)
            }

        if not data.get("success"):
            return data

        provider = data.get("provider_response", {})
        choices = provider.get("choices") or []
        content = None
        if choices:
            content = ((choices[0] or {}).get("message") or {}).get("content")

        return {
            "success": True,
            "mode": data.get("mode"),
            "model": provider.get("model"),
            "content": content,
            "provider_response": provider
        }
