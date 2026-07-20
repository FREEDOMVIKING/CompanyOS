#!/usr/bin/env python3
"""CompanyOS provider-neutral HTTP coder adapter.

Usage contract:
  companyos_http_coder_adapter.py PROMPT_JSON

Required env:
  COMPANYOS_PROVIDER_ENDPOINT
  COMPANYOS_PROVIDER_MODEL

Optional:
  COMPANYOS_CODER_API_KEY

The endpoint receives:
  {"model": "...", "prompt": <CompanyOS JSON payload>}

It must return either:
  {"files":{"relative/path.py":"content"}}
or:
  {"text":"{\\"files\\":{...}}"}
"""

import json, os, sys
from companyos_phase245_252 import HttpProviderAdapter

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: companyos_http_coder_adapter.py PROMPT_JSON")

    endpoint = os.environ.get("COMPANYOS_PROVIDER_ENDPOINT", "").strip()
    model = os.environ.get("COMPANYOS_PROVIDER_MODEL", "").strip()

    if not endpoint or not model:
        print(json.dumps({
            "files": {},
            "metadata": {"error": "provider endpoint/model not configured"}
        }))
        return 2

    payload = json.loads(open(sys.argv[1], "r", encoding="utf-8").read())
    result = HttpProviderAdapter(endpoint, model).invoke(payload)

    if not result.get("success"):
        print(json.dumps({
            "files": {},
            "metadata": {
                "error": result.get("reason", "provider invocation failed")
            }
        }))
        return 3

    print(json.dumps({
        "files": result["files"],
        "metadata": result.get("metadata", {}),
    }))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
