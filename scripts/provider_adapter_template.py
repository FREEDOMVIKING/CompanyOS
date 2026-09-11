#!/usr/bin/env python3
"""
Provider adapter template.

Configure CompanyOS with env vars pointing to provider scripts:

COMPANYOS_DOMAIN_CHECK_CMD
COMPANYOS_DOMAIN_REGISTER_CMD
COMPANYOS_WEB_DEPLOY_CMD
COMPANYOS_DNS_CONFIG_CMD

Each script receives one JSON object on stdin and must emit one JSON object on stdout.

This template intentionally does NOT contain registrar/hosting credentials.
"""
import json, sys

req = json.load(sys.stdin)
action = req.get("action")

if action == "check":
    print(json.dumps({
        "ok": False,
        "reason": "provider_not_implemented",
        "domain": req.get("domain"),
        "available": False
    }))
elif action == "register":
    print(json.dumps({
        "ok": False,
        "reason": "provider_not_implemented"
    }))
elif action == "deploy":
    print(json.dumps({
        "ok": False,
        "reason": "provider_not_implemented"
    }))
elif action == "configure_dns":
    print(json.dumps({
        "ok": False,
        "reason": "provider_not_implemented"
    }))
else:
    print(json.dumps({"ok": False, "reason": "unknown_action"}))
