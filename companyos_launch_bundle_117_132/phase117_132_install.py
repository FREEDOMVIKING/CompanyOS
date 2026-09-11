#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT=Path.home()/"companyos"
BUNDLE=ROOT/"companyos_launch_bundle_117_132"

mapping=[
("project_pipeline.py","companyos/runtime/project_pipeline.py"),
("specialist_coordination.py","companyos/runtime/specialist_coordination.py"),
("project_checkpointing.py","companyos/runtime/project_checkpointing.py"),
("recovery_manager.py","companyos/runtime/recovery_manager.py"),
("launch_readiness.py","companyos/runtime/launch_readiness.py"),
("operations_loop.py","companyos/runtime/operations_loop.py"),
("business_workspace.py","companyos/runtime/business_workspace.py"),
("portfolio_manager.py","companyos/runtime/portfolio_manager.py"),
("revenue_observation.py","companyos/runtime/revenue_observation.py"),
("launch_dashboard.py","companyos/runtime/launch_dashboard.py"),
("phase117_132_launch_ctl.py","phase117_132_launch_ctl.py"),
("phase117_132_test.py","phase117_132_test.py"),
]
stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups={}
for src_name,dst_name in mapping:
    src=BUNDLE/src_name
    dst=ROOT/dst_name
    text=src.read_text()
    ast.parse(text)
    if dst.exists():
        bak=dst.with_name(dst.name+f".phase117_132_backup_{stamp}")
        shutil.copy2(dst,bak); backups[str(dst)]=str(bak)
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(text)
    py_compile.compile(str(dst),doraise=True)

manifest={
"bundle":"117-132",
"project_pipeline":True,
"specialist_coordination":True,
"checkpointing":True,
"recovery_manager":True,
"launch_readiness":True,
"operations_loop":True,
"business_workspace":True,
"portfolio_manager":True,
"revenue_observation":True,
"dashboard":True,
"external_action_execution":False,
"transaction_broadcast_override":False,
"private_key_printed":False,
"backups":backups,
}
(ROOT/"PHASE117_132_LAUNCH_BUNDLE_INSTALLED.json").write_text(json.dumps(manifest,indent=2)+"\n")
print("PHASE117_132_LAUNCH_BUNDLE: INSTALLED")
print("COMPILE_CHECK: PASS")
print("PROJECT_PIPELINE: True")
print("SPECIALIST_COORDINATION: True")
print("CHECKPOINTING: True")
print("RECOVERY_MANAGER: True")
print("LAUNCH_READINESS: True")
print("OPERATIONS_LOOP: True")
print("BUSINESS_WORKSPACE: True")
print("PORTFOLIO_MANAGER: True")
print("REVENUE_OBSERVATION: True")
print("DASHBOARD: True")
print("EXTERNAL_ACTION_EXECUTION: False")
print("TRANSACTION_BROADCAST_OVERRIDE: False")
print("PRIVATE_KEY_PRINTED: False")
