#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT=Path.home()/"companyos"
BUNDLE=ROOT/"companyos_launch_bundle_109_116"
pairs=[
(BUNDLE/"launch_runtime.py",ROOT/"companyos/runtime/launch_runtime.py"),
(BUNDLE/"approval_queue.py",ROOT/"companyos/runtime/approval_queue.py"),
(BUNDLE/"action_proposal_router.py",ROOT/"companyos/runtime/action_proposal_router.py"),
(BUNDLE/"launch_health_snapshot.py",ROOT/"companyos/runtime/launch_health_snapshot.py"),
(BUNDLE/"phase109_116_launch_ctl.py",ROOT/"phase109_116_launch_ctl.py"),
(BUNDLE/"phase109_116_launch_test.py",ROOT/"phase109_116_launch_test.py"),
]
stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups={}
for src,dst in pairs:
    text=src.read_text()
    ast.parse(text)
    if dst.exists():
        bak=dst.with_name(dst.name+f".phase109_116_backup_{stamp}")
        shutil.copy2(dst,bak); backups[str(dst)]=str(bak)
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(text)
    py_compile.compile(str(dst),doraise=True)

manifest={
"bundle":"109-116",
"launch_runtime_control":True,
"approval_queue":True,
"action_proposal_router":True,
"health_snapshot":True,
"unified_start_stop":True,
"external_action_execution":False,
"financial_broadcast_override":False,
"launch_gate":True,
"private_key_printed":False,
"backups":backups,
}
(ROOT/"PHASE109_116_LAUNCH_BUNDLE_INSTALLED.json").write_text(json.dumps(manifest,indent=2)+"\n")
print("PHASE109_116_LAUNCH_BUNDLE: INSTALLED")
print("COMPILE_CHECK: PASS")
print("LAUNCH_RUNTIME_CONTROL: True")
print("APPROVAL_QUEUE: True")
print("ACTION_PROPOSAL_ROUTER: True")
print("HEALTH_SNAPSHOT: True")
print("EXTERNAL_ACTION_EXECUTION: False")
print("PRIVATE_KEY_PRINTED: False")
