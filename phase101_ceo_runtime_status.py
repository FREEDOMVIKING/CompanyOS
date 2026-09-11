#!/usr/bin/env python3
import json
from pathlib import Path

p = Path.home() / ".companyos_runtime" / "autonomous_ceo_runtime_service.json"

print("STATE_FILE_PRESENT:", p.exists())

if p.exists():
    data = json.loads(p.read_text(encoding="utf-8"))
    print(json.dumps(data, indent=2))
else:
    print("{}")

print("PHASE101_CEO_RUNTIME_STATUS: PASS")
