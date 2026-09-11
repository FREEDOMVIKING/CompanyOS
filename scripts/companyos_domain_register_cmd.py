#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
bridge = Path.home() / "companyos" / "scripts" / "companyos_real_launch_provider_bridge.py"
req = json.load(sys.stdin)
req["action"] = "register"
p = subprocess.run([sys.executable, str(bridge)], input=json.dumps(req), text=True, capture_output=True)
sys.stdout.write(p.stdout)
sys.stderr.write(p.stderr)
raise SystemExit(p.returncode)
