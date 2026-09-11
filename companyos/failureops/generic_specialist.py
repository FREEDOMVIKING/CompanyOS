import json
import os
import urllib.request

class GenericSpecialist:
    def __init__(self, root):
        self.root = root
        self.url = os.getenv("COMPANYOS_REASONING_URL", "http://127.0.0.1:8765/reason")

    def execute(self, job, department="operations"):
        payload = job.get("payload", {})
        prompt = {
            "job_kind": job.get("kind"),
            "department": department,
            "instruction": payload.get("instruction") or payload,
            "success_criteria": payload.get("success_criteria", []),
            "constraint": "Perform bounded internal analysis only. Do not claim external side effects."
        }
        req = urllib.request.Request(
            self.url,
            data=json.dumps({
                "messages":[
                    {"role":"system","content":"You are CompanyOS generic recovery specialist. Complete bounded internal analysis for unsupported internal jobs. Return a concise actionable result. Do not perform or claim external actions."},
                    {"role":"user","content":json.dumps(prompt,default=str)}
                ]
            }).encode(),
            headers={"Content-Type":"application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8","replace"))
        except Exception as exc:
            return {"success":False,"error":type(exc).__name__,"message":str(exc)}

        if not data.get("success"):
            return data

        provider = data.get("provider_response", {})
        choices = provider.get("choices") or []
        content = None
        if choices:
            content = ((choices[0] or {}).get("message") or {}).get("content")

        return {
            "success": True,
            "capability": "generic_recovery_specialist",
            "department": department,
            "kind": job.get("kind"),
            "analysis": content,
            "model": provider.get("model"),
            "external_side_effects": False
        }
