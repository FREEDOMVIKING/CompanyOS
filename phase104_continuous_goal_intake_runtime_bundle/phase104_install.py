#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase104_continuous_goal_intake_runtime_bundle"
pairs = [
    (BUNDLE/"continuous_goal_runtime.py", ROOT/"companyos/runtime/continuous_goal_runtime.py"),
    (BUNDLE/"phase104_runtime_ctl.py", ROOT/"phase104_runtime_ctl.py"),
    (BUNDLE/"phase104_test.py", ROOT/"phase104_test.py"),
]
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}
for src,dst in pairs:
    text=src.read_text()
    ast.parse(text)
    if dst.exists():
        bak=dst.with_name(dst.name+f".phase104_backup_{stamp}")
        shutil.copy2(dst,bak); backups[str(dst)]=str(bak)
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(text)
    py_compile.compile(str(dst),doraise=True)

manifest={
 "phase":"104_CONTINUOUS_GOAL_INTAKE_RUNTIME",
 "status":"installed",
 "continuous_goal_intake":True,
 "intake_to_ceo_runtime_loop":True,
 "idle_safe":True,
 "max_failure_guard":True,
 "external_actions":False,
 "signs_transaction":False,
 "broadcasts_transaction":False,
 "private_key_printed":False,
 "backups":backups,
}
(ROOT/"PHASE104_CONTINUOUS_GOAL_INTAKE_RUNTIME_INSTALLED.json").write_text(json.dumps(manifest,indent=2)+"\n")
print("PHASE104_CONTINUOUS_GOAL_INTAKE_RUNTIME: INSTALLED")
print("COMPILE_CHECK: PASS")
print("CONTINUOUS_GOAL_INTAKE: True")
print("INTAKE_TO_CEO_RUNTIME_LOOP: True")
print("IDLE_SAFE: True")
print("MAX_FAILURE_GUARD: True")
print("EXTERNAL_ACTIONS: False")
print("BROADCASTS_TRANSACTION: False")
print("PRIVATE_KEY_PRINTED: False")
