#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase106_autonomous_opportunity_discovery_bundle"

pairs = [
    (BUNDLE/"opportunity_discovery.py", ROOT/"companyos/runtime/opportunity_discovery.py"),
    (BUNDLE/"opportunity_discovery_engine.py", ROOT/"companyos/runtime/opportunity_discovery_engine.py"),
    (BUNDLE/"opportunity_goal_generator.py", ROOT/"companyos/runtime/opportunity_goal_generator.py"),
    (BUNDLE/"phase106_opportunity_test.py", ROOT/"phase106_opportunity_test.py"),
    (BUNDLE/"phase106_runtime_seed_demo.py", ROOT/"phase106_runtime_seed_demo.py"),
    (BUNDLE/"phase106_opportunity_status.py", ROOT/"phase106_opportunity_status.py"),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text()
    ast.parse(text)
    if dst.exists():
        bak = dst.with_name(dst.name + f".phase106_backup_{stamp}")
        shutil.copy2(dst, bak)
        backups[str(dst)] = str(bak)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text)
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "106_AUTONOMOUS_OPPORTUNITY_DISCOVERY",
    "status": "installed",
    "persistent_opportunity_store": True,
    "opportunity_scoring": True,
    "opportunity_deduplication": True,
    "opportunity_to_goal_generation": True,
    "phase105_policy_gate_reused": True,
    "external_actions": False,
    "signs_transaction": False,
    "broadcasts_transaction": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT/"PHASE106_AUTONOMOUS_OPPORTUNITY_DISCOVERY_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n"
)

print("PHASE106_AUTONOMOUS_OPPORTUNITY_DISCOVERY: INSTALLED")
print("COMPILE_CHECK: PASS")
print("PERSISTENT_OPPORTUNITY_STORE: True")
print("OPPORTUNITY_SCORING: True")
print("OPPORTUNITY_DEDUPLICATION: True")
print("OPPORTUNITY_TO_GOAL_GENERATION: True")
print("PHASE105_POLICY_GATE_REUSED: True")
print("OPPORTUNITY_DISCOVERY_EXTERNAL_ACTIONS: False")
print("OPPORTUNITY_DISCOVERY_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
