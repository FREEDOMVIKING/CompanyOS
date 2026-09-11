import json
import os
import urllib.request

class BaseSpecialist:
    def __init__(self, root):
        self.root = root
        self.reasoning_url = os.getenv(
            "COMPANYOS_REASONING_URL",
            "http://127.0.0.1:8765/reason"
        )

    def ask_ai(self, system, task, timeout=90):
        payload = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(task, default=str)}
            ]
        }
        req = urllib.request.Request(
            self.reasoning_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8", "replace"))
        except Exception as exc:
            return {"success": False, "error": type(exc).__name__, "message": str(exc)}

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
        }
