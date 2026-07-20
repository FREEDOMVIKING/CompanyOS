#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from companyos_phase253_260 import OpenRouterCoderAdapter

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: companyos_openrouter_coder.py PROMPT_JSON")
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    result = OpenRouterCoderAdapter().generate(payload)
    if not result.get("success"):
        print(json.dumps({"files": {}, "metadata": {"success": False, "reason": result.get("reason"), "attempts": result.get("attempts", [])}}))
        return 2
    print(json.dumps({
        "files": result["files"],
        "metadata": {
            "success": True,
            "model": result.get("model"),
            "usage": result.get("usage", {}),
            **result.get("metadata", {}),
        },
    }))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
