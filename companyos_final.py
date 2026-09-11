#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from companyos_modules.final_consolidation.runtime import CompanyOSConsolidatedRuntime


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["status", "verify", "demo"])
    args = parser.parse_args()

    runtime = CompanyOSConsolidatedRuntime()
    if args.action == "status":
        result = runtime.integration_state()
    elif args.action == "verify":
        result = runtime.verify()
    else:
        result = runtime.demo()

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok", result.get("core_ready", False)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
