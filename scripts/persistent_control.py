#!/usr/bin/env python3
import json, sys
from pathlib import Path
from companyos_phase285_292 import ResumeController

root = Path.home() / "companyos"
ctl = ResumeController(root)
cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

if cmd == "pause":
    result = ctl.pause()
elif cmd == "resume":
    result = ctl.resume()
else:
    result = ctl.status()

print(json.dumps(result, indent=2))
