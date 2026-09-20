from pathlib import Path
import json
import subprocess

ROOT=Path.home()/"companyos"

def load_manifest():
    return json.loads((ROOT/"audit/COMPANYOS_V67_2_HISTORY_EXTRACTION_MANIFEST.json").read_text())

def tracked():
    cp=subprocess.run(["git","ls-files"],cwd=ROOT,text=True,capture_output=True,check=True)
    return set(cp.stdout.splitlines())

def test_history_extraction_manifest_is_recoverable():
    d=load_manifest()
    assert d["files_removed_from_active_branch"] == 1126
    assert d["recovery_branch"].startswith("recovery/v67.2b-pre-history-extraction-")
    assert d["canonical_runtime_files_targeted"] is False
    assert d["financial_limits_changed"] is False

def test_removed_history_is_not_in_active_index():
    d=load_manifest()
    now=tracked()
    sample=d["paths"][:100]
    assert sample
    assert all(row["path"] not in now for row in sample)

def test_full_audit_will_not_reimport_patch_history_by_default():
    s=(ROOT/"scripts/companyos_full_sync_audit.sh").read_text()
    assert "PATCH_HISTORY_IMPORT=DISABLED_BY_DEFAULT" in s
    assert "COMPANYOS_COMMIT_PATCH_HISTORY" in s

def test_canonical_control_plane_remains_present():
    required=[
        "companyos/runtime/service_supervisor.py",
        "companyos/runtime/runtime_control.py",
        "scripts/companyosctl",
        "config/companyos_active_component_manifest.json",
    ]
    assert all((ROOT/p).exists() for p in required)
