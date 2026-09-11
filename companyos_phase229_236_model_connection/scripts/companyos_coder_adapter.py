#!/usr/bin/env python3
"""Generic CompanyOS coder adapter contract.

This file is intentionally provider-neutral.
Set COMPANYOS_PROVIDER_ADAPTER_CMD to a command that:
  1) accepts a single prompt JSON file path argument
  2) prints JSON: {"files": {"relative/path.py": "content"}}

Then set:
  export COMPANYOS_CODER_CMD="python ~/companyos/scripts/companyos_coder_adapter.py"

The adapter forwards the prompt to COMPANYOS_PROVIDER_ADAPTER_CMD.
"""

import json, os, shlex, subprocess, sys

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: companyos_coder_adapter.py PROMPT_JSON")

    provider_cmd = os.environ.get("COMPANYOS_PROVIDER_ADAPTER_CMD", "").strip()
    if not provider_cmd:
        print(json.dumps({
            "files": {},
            "metadata": {"error": "COMPANYOS_PROVIDER_ADAPTER_CMD not configured"}
        }))
        return 2

    p = subprocess.run(
        shlex.split(provider_cmd) + [sys.argv[1]],
        text=True,
        capture_output=True,
        timeout=600,
        check=False,
        env=os.environ.copy(),
    )
    if p.returncode != 0:
        print(json.dumps({
            "files": {},
            "metadata": {
                "error": "provider adapter failed",
                "stderr": p.stderr[-8000:]
            }
        }))
        return p.returncode

    # Provider command must already return the CompanyOS file contract.
    sys.stdout.write(p.stdout)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
