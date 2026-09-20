from pathlib import Path
import json
import subprocess

ROOT=Path.home()/"companyos"

def manifest():
    return json.loads((ROOT/"audit/COMPANYOS_V67_3_LEGACY_BATCH1_MANIFEST.json").read_text())

def tracked():
    cp=subprocess.run(["git","ls-files"],cwd=ROOT,text=True,capture_output=True,check=True)
    return set(cp.stdout.splitlines())

def test_batch_is_recoverable_and_zero_reference():
    d=manifest()
    assert d["selected_root_count"] > 0
    assert d["files_removed_from_active_branch"] > 0
    assert d["recovery_branch"].startswith("recovery/v67.3b-pre-legacy-batch1-")
    assert d["current_reference_recheck"] == "PASS_ZERO_ACTIVE_SOURCE_HITS"
    assert d["canonical_runtime_files_targeted"] is False
    assert d["financial_limits_changed"] is False

def test_selected_paths_are_not_in_active_index():
    d=manifest()
    now=tracked()
    selected=[p for row in d["selected_roots"] for p in row["files"]]
    assert selected
    assert all(p not in now for p in selected)

def test_canonical_runtime_surface_still_exists():
    required=[
        "companyos/runtime/service_supervisor.py",
        "companyos/runtime/runtime_control.py",
        "companyos/runtime/autonomous_task_queue.py",
        "companyos/runtime/profit_opportunity_engine.py",
        "companyos/connectors/hosting_router.py",
        "scripts/companyosctl",
        "config/companyos_active_component_manifest.json",
    ]
    assert all((ROOT/p).exists() for p in required)
