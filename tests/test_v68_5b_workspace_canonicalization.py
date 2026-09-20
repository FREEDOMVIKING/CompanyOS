from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT=Path.home()/"companyos"
UPPER=ROOT/"workspace/Local_Contractor_Bid_Organizer"
LOWER=ROOT/"workspace/local_contractor_bid_organizer"
PROGRESS=UPPER/"companyos_progress"

def manifest():
    return json.loads((ROOT/"audit/COMPANYOS_V68_5B_WORKSPACE_CANONICALIZATION_MANIFEST.json").read_text())

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def test_lowercase_workspace_is_active_canonical():
    assert LOWER.is_dir()
    assert not LOWER.is_symlink()
    assert (LOWER/"prototype/current/server.py").exists()
    assert (LOWER/"customer_problem_validation.md").exists()
    assert (LOWER/"product_requirements.md").exists()

def test_uppercase_container_keeps_progress_but_active_paths_are_symlinks():
    assert UPPER.is_dir()
    assert not UPPER.is_symlink()
    assert PROGRESS.is_dir()

    expected={
        "prototype":"../local_contractor_bid_organizer/prototype",
        "customer_problem_validation.md":"../local_contractor_bid_organizer/customer_problem_validation.md",
        "product_requirements.md":"../local_contractor_bid_organizer/product_requirements.md",
    }
    for rel,target in expected.items():
        p=UPPER/rel
        assert p.is_symlink()
        assert os.readlink(p)==target
        assert p.exists()

def test_all_pre_migration_active_content_is_preserved():
    d=manifest()
    assert d["same_relative_file_count"]==8
    assert d["migrated_unique_file_count"]==2

    for rel,meta in d["pre_migration_upper_active_hashes"].items():
        assert (LOWER/rel).exists()
        assert sha(LOWER/rel)==meta["sha256"]
        assert (UPPER/rel).exists()
        assert sha(UPPER/rel)==meta["sha256"]

def test_progress_history_is_byte_preserved():
    d=manifest()
    assert d["progress_file_count"]>0
    assert d["progress_history_rewritten"] is False

    for rel,meta in d["pre_migration_progress_hashes"].items():
        p=PROGRESS/rel
        assert p.exists()
        assert sha(p)==meta["sha256"]

def test_git_tracks_only_three_active_compatibility_symlinks_under_upper_root():
    expected={
        "workspace/Local_Contractor_Bid_Organizer/prototype",
        "workspace/Local_Contractor_Bid_Organizer/customer_problem_validation.md",
        "workspace/Local_Contractor_Bid_Organizer/product_requirements.md",
    }
    for rel in expected:
        cp=subprocess.run(
            ["git","ls-files","-s","--",rel],
            cwd=ROOT,text=True,capture_output=True,check=True
        )
        line=cp.stdout.strip()
        assert line.startswith("120000 ")
        assert line.endswith("\t"+rel)

    cp=subprocess.run(
        ["git","ls-files","--","workspace/Local_Contractor_Bid_Organizer/prototype/"],
        cwd=ROOT,text=True,capture_output=True,check=True
    )
    assert cp.stdout.strip()==""

def test_operational_lowercase_references_remain():
    install=(ROOT/"install_phase15_step6.sh").read_text(errors="ignore")
    registry=(ROOT/"ceo_memory/prototype_registry.json").read_text(errors="ignore")
    health=(ROOT/"ceo_memory/prototype_builder_health.json").read_text(errors="ignore")
    assert "workspace/local_contractor_bid_organizer/prototype/current/server.py" in install
    assert "/workspace/local_contractor_bid_organizer/prototype/current" in registry
    assert "/workspace/local_contractor_bid_organizer/prototype/current" in health

def test_semantic_groups_untouched():
    assert manifest()["semantic_duplicate_groups_changed"] is False

def test_canonical_runtime_surface_remains():
    required=[
        "companyos/runtime/service_supervisor.py",
        "companyos/runtime/runtime_control.py",
        "companyos/runtime/autonomous_task_queue.py",
        "companyos/runtime/profit_opportunity_engine.py",
        "companyos/connectors/hosting_router.py",
        "config/companyos_active_component_manifest.json",
    ]
    assert all((ROOT/p).exists() for p in required)
